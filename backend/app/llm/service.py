"""Сервис чата — оркестрация LLM + ЭС + RAG.

Поток:
1. Студент отправляет сообщение
2. LLM получает: системный промпт + профиль + история + сообщение
3. LLM решает: вызвать функцию (ЭС/RAG) или ответить напрямую
4. Если function call → выполняем → передаём результат LLM
5. LLM формирует финальный ответ
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import select

from app.config import settings
from app.db.database import async_session_factory
from app.db.models import LLMTrace, User
from app.llm.client import OpenRouterClient
from app.llm.prompts import (
    SYSTEM_PROMPT,
    TOOL_DEFINITIONS,
    build_profile_context,
    format_recommendations_for_llm,
)
from app.llm.schemas import DebugInfo, TraceDetail, TraceSummary

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.expert.schemas import StudentProfile

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 3  # Максимум итераций function calling


@dataclass
class ChatDebugInfo:
    """Отладочные данные для debug-чата админа."""

    rules_fired: list[str] = field(default_factory=list)
    rag_chunks: list[str] = field(default_factory=list)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    profile_changes: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatResult:
    """Результат обработки сообщения."""

    reply: str
    debug: ChatDebugInfo | None = None


class ChatService:
    """Оркестратор чата: связывает LLM, ЭС и RAG."""

    def __init__(self, llm_client: OpenRouterClient | None = None) -> None:
        self._llm = llm_client or OpenRouterClient()

    async def process_message(
        self,
        message: str,
        profile: StudentProfile,
        history: list[dict[str, str]] | None = None,
        *,
        debug: bool = False,
    ) -> ChatResult:
        """Обработка сообщения студента.

        Args:
            message: текст сообщения
            profile: текущий профиль студента
            history: последние 4-5 пар сообщений
            debug: включить отладочную информацию (для админа)
        """
        debug_info = ChatDebugInfo() if debug else None
        profile_data = profile.model_dump(mode="json")

        # Собираем сообщения для LLM
        messages = self._build_messages(message, profile_data, history)

        # Цикл function calling (LLM может вызвать несколько функций)
        for _ in range(MAX_TOOL_ROUNDS):
            response = await self._llm.chat(messages, tools=TOOL_DEFINITIONS)
            tool_calls = OpenRouterClient.extract_tool_calls(response)

            if not tool_calls:
                # LLM ответила без function call — финальный ответ
                reply = OpenRouterClient.extract_content(response)
                return ChatResult(reply=reply, debug=debug_info)

            # Обработка function calls
            assistant_msg = response["choices"][0]["message"]
            messages.append(assistant_msg)

            for tool_call in tool_calls:
                fn_name = tool_call["function"]["name"]
                fn_args = OpenRouterClient.parse_tool_arguments(tool_call)
                tool_id = tool_call["id"]

                if debug_info is not None:
                    debug_info.tool_calls.append({"function": fn_name, "args": fn_args})

                result = await self._execute_function(fn_name, fn_args, profile, debug_info)

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": result,
                    }
                )

        # Если исчерпали лимит итераций — запрашиваем финальный ответ без tools
        response = await self._llm.chat(messages)
        reply = OpenRouterClient.extract_content(response)
        return ChatResult(reply=reply, debug=debug_info)

    async def _execute_function(
        self,
        fn_name: str,
        fn_args: dict[str, Any],
        profile: StudentProfile,
        debug_info: ChatDebugInfo | None,
    ) -> str:
        """Выполнение function call от LLM."""
        if fn_name == "get_recommendations":
            return await self._fn_get_recommendations(profile, debug_info)

        if fn_name == "recalculate_with_changes":
            return await self._fn_recalculate(profile, fn_args, debug_info)

        if fn_name == "search_knowledge":
            return await self._fn_search_knowledge(fn_args, debug_info)

        return f"Неизвестная функция: {fn_name}"

    async def _fn_get_recommendations(
        self,
        profile: StudentProfile,
        debug_info: ChatDebugInfo | None,
    ) -> str:
        """get_recommendations: рекомендации по текущему профилю."""
        from app.expert.service import expert_service

        if debug_info is not None:
            trace, recs = expert_service.get_recommendations_debug(profile)
            debug_info.rules_fired = trace.rules_fired_ids
        else:
            recs = expert_service.get_recommendations(profile)

        return format_recommendations_for_llm([r.model_dump() for r in recs])

    async def _fn_recalculate(
        self,
        profile: StudentProfile,
        changes: dict[str, Any],
        debug_info: ChatDebugInfo | None,
    ) -> str:
        """recalculate_with_changes: пересчёт с изменением параметров."""
        from app.expert.service import expert_service

        # Применяем изменения к копии профиля
        profile_data = profile.model_dump()
        allowed_changes = {"career_goal", "technopark_status", "workload_pref"}
        applied: dict[str, Any] = {}

        for key, value in changes.items():
            if key in allowed_changes:
                profile_data[key] = value
                applied[key] = value

        if debug_info is not None:
            debug_info.profile_changes = applied

        # Пересоздаём профиль с изменениями
        from app.expert.schemas import StudentProfile as StudentProfileModel

        modified_profile = StudentProfileModel(**profile_data)

        if debug_info is not None:
            trace, recs = expert_service.get_recommendations_debug(modified_profile)
            debug_info.rules_fired = trace.rules_fired_ids
        else:
            recs = expert_service.get_recommendations(modified_profile)

        changes_text = ", ".join(f"{k}={v}" for k, v in applied.items())
        header = f"Пересчёт с изменениями: {changes_text}\n\n"
        return header + format_recommendations_for_llm([r.model_dump() for r in recs])

    async def _fn_search_knowledge(
        self,
        args: dict[str, Any],
        debug_info: ChatDebugInfo | None,
    ) -> str:
        """search_knowledge: семантический поиск по RAG."""
        from app.rag.service import rag_service

        query = args.get("query", "")

        try:
            chunks = await rag_service.search(query, top_k=5)
        except Exception as exc:
            logger.warning("RAG поиск недоступен: %s", exc)
            chunks = []

        if debug_info is not None:
            debug_info.rag_chunks = [f"{c.source}: {c.content[:100]}" for c in chunks]

        if not chunks:
            return (
                f"По запросу '{query}' ничего не найдено в базе знаний. "
                "Ответь на основе общих знаний или предложи уточнить вопрос."
            )

        lines = [f"Результаты поиска по запросу '{query}':"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(f"\n[{i}] Источник: {chunk.source} (релевантность: {chunk.score:.2f})")
            lines.append(chunk.content)
        return "\n".join(lines)

    def _build_messages(
        self,
        message: str,
        profile_data: dict[str, Any],
        history: list[dict[str, str]] | None,
    ) -> list[dict[str, Any]]:
        """Сборка списка сообщений для LLM."""
        profile_context = build_profile_context(profile_data)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "system", "content": profile_context},
        ]

        # Последние 4-5 пар из истории
        if history:
            for msg in history[-10:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": message})
        return messages


chat_service = ChatService()


# ── Журнал LLM-трейсов (admin) ────────────────────────────────────────────


async def write_trace(
    *,
    user_id: uuid.UUID,
    endpoint: str,
    request_message: str,
    response_text: str,
    debug: ChatDebugInfo | None,
    latency_ms: int,
    status: str,
) -> None:
    """Записать одну запись в `llm_traces`.

    Запускается через BackgroundTasks после возврата ответа клиенту, чтобы
    не блокировать handler. Открывает собственную короткую сессию.
    """
    debug_payload: dict[str, Any] | None = None
    if debug is not None:
        debug_payload = {
            "rules_fired": debug.rules_fired,
            "rag_chunks": debug.rag_chunks,
            "tool_calls": debug.tool_calls,
            "profile_changes": debug.profile_changes,
        }

    try:
        async with async_session_factory() as db:
            trace = LLMTrace(
                user_id=user_id,
                endpoint=endpoint,
                request_message=request_message,
                response_text=response_text,
                debug=debug_payload,
                latency_ms=latency_ms,
                status=status,
                model_name=settings.llm_model,
            )
            db.add(trace)
            await db.commit()
    except Exception:
        # Журнал — best effort: ошибка записи не должна валить запрос.
        # Cancellation/SystemExit пробрасываем — они должны уметь останавливать
        # фоновую задачу при shutdown'е сервера.
        logger.exception("Не удалось записать LLM-трейс")


async def list_traces(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[TraceSummary]:
    """Список трейсов с фильтрами user_id / date_from / date_to и пагинацией.

    `date_to` интерпретируется как «по конец указанного дня включительно»:
    если фронт прислал `2026-05-04T00:00:00`, фильтр захватит весь день до
    `2026-05-05T00:00:00`. Это соответствует ожиданию date-picker'а.
    """
    stmt = (
        select(LLMTrace, User.email)
        .join(User, User.id == LLMTrace.user_id)
        .order_by(LLMTrace.created_at.desc())
    )
    if user_id is not None:
        stmt = stmt.where(LLMTrace.user_id == user_id)
    if date_from is not None:
        stmt = stmt.where(LLMTrace.created_at >= date_from)
    if date_to is not None:
        # Полночь date_to → захватываем весь этот день (< следующий день)
        end = (
            date_to + timedelta(days=1)
            if date_to.hour == 0 and date_to.minute == 0 and date_to.second == 0
            else date_to
        )
        stmt = stmt.where(LLMTrace.created_at < end)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.all()

    summaries: list[TraceSummary] = []
    for trace, email in rows:
        rules_fired = (trace.debug or {}).get("rules_fired") or []
        summaries.append(
            TraceSummary(
                id=trace.id,
                created_at=trace.created_at,
                user_email=email,
                endpoint=trace.endpoint,
                latency_ms=trace.latency_ms,
                status=trace.status,
                rules_fired_count=len(rules_fired),
                request_preview=trace.request_message[:80],
            )
        )
    return summaries


async def get_trace(trace_id: uuid.UUID, db: AsyncSession) -> TraceDetail | None:
    """Полная запись трейса с email пользователя."""
    result = await db.execute(select(LLMTrace).where(LLMTrace.id == trace_id))
    trace = result.scalar_one_or_none()
    if trace is None:
        return None

    user_email = await db.scalar(select(User.email).where(User.id == trace.user_id))

    debug = None
    if trace.debug:
        debug = DebugInfo(
            rules_fired=trace.debug.get("rules_fired") or [],
            rag_chunks=trace.debug.get("rag_chunks") or [],
            tool_calls=trace.debug.get("tool_calls") or [],
            profile_changes=trace.debug.get("profile_changes") or {},
        )

    return TraceDetail(
        id=trace.id,
        created_at=trace.created_at,
        user_id=trace.user_id,
        user_email=user_email or "",
        endpoint=trace.endpoint,
        request_message=trace.request_message,
        response_text=trace.response_text,
        debug=debug,
        latency_ms=trace.latency_ms,
        status=trace.status,
        model_name=trace.model_name,
    )
