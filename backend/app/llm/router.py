"""Роутер чата — студенческий и debug для админа."""

from __future__ import annotations

from fastapi import APIRouter

from app.db.database import async_session_factory
from app.dependencies import CurrentAdmin, CurrentUser
from app.llm.schemas import ChatRequest, ChatResponse, DebugInfo
from app.llm.service import chat_service
from app.users.profile_builder import build_student_profile

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(body: ChatRequest, user: CurrentUser) -> ChatResponse:
    """Отправка сообщения в чат (студент)."""
    # Короткая сессия только под построение профиля; LLM-вызов идёт без DB connection
    async with async_session_factory() as db:
        profile = await build_student_profile(user, db)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    result = await chat_service.process_message(
        message=body.message, profile=profile, history=history
    )
    return ChatResponse(reply=result.reply)


@router.post("/message/debug", response_model=ChatResponse)
async def send_message_debug(body: ChatRequest, admin: CurrentAdmin) -> ChatResponse:
    """Отправка сообщения в debug-чат (админ). Возвращает отладочные данные."""
    async with async_session_factory() as db:
        profile = await build_student_profile(admin, db)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    result = await chat_service.process_message(
        message=body.message, profile=profile, history=history, debug=True
    )

    debug = None
    if result.debug:
        debug = DebugInfo(
            rules_fired=result.debug.rules_fired,
            rag_chunks=result.debug.rag_chunks,
            tool_calls=result.debug.tool_calls,
            profile_changes=result.debug.profile_changes,
        )

    return ChatResponse(reply=result.reply, debug=debug)
