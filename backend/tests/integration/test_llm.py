"""Integration-тесты модуля чата (LLM-оркестратор).

Используется `fake_llm` (FIFO очередь ответов) и реальная ЭС поверх seed-данных.
Внешние API не дёргаются.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.rag.service import rag_service

from tests.integration._fakes import FakeEmbeddingClient, FakeLLMClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
def _clean_rag_for_chat(fake_embedder: FakeEmbeddingClient) -> None:
    """Очистка Qdrant и BM25 до и после чат-тестов (на случай search_knowledge)."""
    try:
        all_sources = rag_service._qdrant.scroll_all_content()
        for source in all_sources:
            rag_service._qdrant.delete_by_source(source)
    except Exception:
        pass
    rag_service._all_chunks = []
    if hasattr(rag_service, "_source_chunks_map"):
        rag_service._source_chunks_map = {}
    rag_service._bm25.fit([])


class TestChatMessage:
    async def test_simple_text_reply(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """LLM возвращает текст без function call — ответ ретранслируется."""
        fake_llm.queue_text("привет, я твой навигатор")

        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "привет"},
        )
        assert response.status_code == 200
        assert response.json()["reply"] == "привет, я твой навигатор"
        assert len(fake_llm.calls) == 1

    async def test_function_call_get_recommendations(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """tool_call get_recommendations → ЭС → tool result → финальный текст LLM."""
        fake_llm.queue_tool_call("get_recommendations", "{}")
        fake_llm.queue_text("итоговый ответ от LLM")

        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "что мне выбрать?"},
        )
        assert response.status_code == 200
        assert response.json()["reply"] == "итоговый ответ от LLM"

        # Должно быть ровно 2 вызова LLM
        assert len(fake_llm.calls) == 2

        # Во втором вызове в messages должен быть tool result
        second_msgs = fake_llm.calls[1]["messages"]
        tool_msgs = [m for m in second_msgs if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        # Результат ЭС содержит характерный заголовок (или сообщение об отсутствии)
        content = tool_msgs[0]["content"]
        assert (
            "Результат экспертной системы" in content
            or "Экспертная система не выдала рекомендаций" in content
        )

    async def test_function_call_search_knowledge(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        admin_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """tool_call search_knowledge → RAG → tool result → финальный текст."""
        # Загружаем документ заранее (admin) — fake_embedder подставлен автофикстурой
        upload = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "ml_intro.txt", "text": "Машинное обучение — это интересно."},
        )
        assert upload.status_code == 201

        fake_llm.queue_tool_call("search_knowledge", '{"query":"ml"}')
        fake_llm.queue_text("вот что я нашёл")

        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "расскажи про ml"},
        )
        assert response.status_code == 200
        assert response.json()["reply"] == "вот что я нашёл"
        assert len(fake_llm.calls) == 2

        # Tool message должен содержать результат RAG-поиска
        tool_msgs = [m for m in fake_llm.calls[1]["messages"] if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        # Если что-то нашлось — увидим характерное «Результаты поиска», иначе «ничего не найдено»
        content = tool_msgs[0]["content"]
        assert "Результаты поиска" in content or "ничего не найдено" in content

    async def test_function_call_recalculate_with_changes(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """tool_call recalculate_with_changes → ЭС с изменённой целью."""
        fake_llm.queue_tool_call(
            "recalculate_with_changes", '{"career_goal":"backend"}'
        )
        fake_llm.queue_text("пересчитал для бэкенда")

        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "а если бэкенд?"},
        )
        assert response.status_code == 200
        assert response.json()["reply"] == "пересчитал для бэкенда"
        assert len(fake_llm.calls) == 2

        tool_msgs = [m for m in fake_llm.calls[1]["messages"] if m.get("role") == "tool"]
        assert len(tool_msgs) == 1
        content = tool_msgs[0]["content"]
        # Заголовок содержит изменения, переданные в recalculate
        assert "career_goal=backend" in content
        assert (
            "Результат экспертной системы" in content
            or "Экспертная система не выдала рекомендаций" in content
        )

    async def test_max_tool_rounds_limit(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """Если LLM упорно зовёт функции — цикл обрывается на MAX_TOOL_ROUNDS=3.

        3 итерации с tools исчерпают эти ответы, 4-й chat() уже без tools — берёт текст.
        """
        for _ in range(3):
            fake_llm.queue_tool_call("get_recommendations", "{}")
        fake_llm.queue_text("финал после лимита")

        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "зацикливайся"},
        )
        assert response.status_code == 200
        # Всего вызовов LLM — 3 раза с tools + 1 финальный = 4
        assert len(fake_llm.calls) == 4
        # Последний вызов идёт без tools
        assert fake_llm.calls[-1]["tools"] is None
        assert response.json()["reply"] == "финал после лимита"

    async def test_history_passed_to_llm(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """История диалога передаётся в messages первого вызова."""
        fake_llm.queue_text("ответ")

        history = [
            {"role": "user", "content": "первый вопрос"},
            {"role": "assistant", "content": "первый ответ"},
        ]
        response = await client.post(
            "/api/v1/chat/message",
            headers=student_auth,
            json={"message": "новый вопрос", "history": history},
        )
        assert response.status_code == 200

        msgs = fake_llm.calls[0]["messages"]
        contents = [m.get("content", "") for m in msgs]
        assert "первый вопрос" in contents
        assert "первый ответ" in contents
        assert "новый вопрос" in contents

    async def test_unauthenticated_returns_401(self, client: AsyncClient) -> None:
        """Без токена — 401."""
        response = await client.post(
            "/api/v1/chat/message", json={"message": "привет"}
        )
        assert response.status_code == 401


class TestChatDebug:
    async def test_debug_forbidden_for_student(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        fake_llm: FakeLLMClient,
    ) -> None:
        """Студент не имеет доступа к /chat/message/debug — 403."""
        fake_llm.queue_text("ok")
        response = await client.post(
            "/api/v1/chat/message/debug",
            headers=student_auth,
            json={"message": "привет"},
        )
        assert response.status_code == 403

    async def test_debug_returns_debug_info(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        fake_llm: FakeLLMClient,
        seeded: None,
    ) -> None:
        """Debug-эндпоинт возвращает поле debug со всеми вложенными списками."""
        fake_llm.queue_tool_call("get_recommendations", "{}")
        fake_llm.queue_text("готово")

        response = await client.post(
            "/api/v1/chat/message/debug",
            headers=admin_auth,
            json={"message": "что выбрать?"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["reply"] == "готово"
        assert body["debug"] is not None
        debug = body["debug"]
        assert "rules_fired" in debug
        assert "rag_chunks" in debug
        assert "tool_calls" in debug
        assert "profile_changes" in debug

        # Был tool_call — он должен попасть в debug.tool_calls
        assert len(debug["tool_calls"]) == 1
        assert debug["tool_calls"][0]["function"] == "get_recommendations"
