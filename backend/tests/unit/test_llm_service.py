"""Тесты LLM-модуля: клиент, промпты, оркестрация.

Все тесты без реальных HTTP-запросов — используем моки.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.db.models import CareerGoal
from app.llm.client import OpenRouterClient
from app.llm.prompts import (
    TOOL_DEFINITIONS,
    build_profile_context,
    format_recommendations_for_llm,
)
from app.llm.service import ChatService
from tests.conftest import make_profile

# ── Тесты промптов ──────────────────────────────────────────────────────────


class TestPrompts:
    def test_tool_definitions_has_three_functions(self) -> None:
        assert len(TOOL_DEFINITIONS) == 3
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        assert names == {"get_recommendations", "recalculate_with_changes", "search_knowledge"}

    def test_recalculate_params_are_enums(self) -> None:
        """recalculate_with_changes должен иметь enum для всех параметров."""
        fn = next(
            t for t in TOOL_DEFINITIONS if t["function"]["name"] == "recalculate_with_changes"
        )
        props = fn["function"]["parameters"]["properties"]
        assert "enum" in props["career_goal"]
        assert "enum" in props["technopark_status"]
        assert "enum" in props["workload_pref"]
        assert len(props["career_goal"]["enum"]) == 11
        assert len(props["technopark_status"]["enum"]) == 5
        assert len(props["workload_pref"]["enum"]) == 3

    def test_build_profile_context(self) -> None:
        profile = make_profile(career_goal=CareerGoal.ML, semester=4, weak_math=True)
        ctx = build_profile_context(profile.model_dump(mode="json"))
        assert "ML / Data Science" in ctx
        assert "4" in ctx
        assert "математике" in ctx

    def test_format_recommendations_empty(self) -> None:
        result = format_recommendations_for_llm([])
        assert "не выдала" in result

    def test_format_recommendations_with_data(self) -> None:
        recs = [
            {
                "rule_id": "R1",
                "category": "ck_course",
                "title": "Инженер ML",
                "priority": "high",
                "reasoning": "Тест",
                "competency_gap": "ml_basics",
            }
        ]
        result = format_recommendations_for_llm(recs)
        assert "Инженер ML" in result
        assert "R1" in result
        assert "ml_basics" in result


# ── Тесты клиента ───────────────────────────────────────────────────────────


class TestOpenRouterClient:
    def test_extract_content(self) -> None:
        response = {"choices": [{"message": {"content": "Привет!"}}]}
        assert OpenRouterClient.extract_content(response) == "Привет!"

    def test_extract_content_empty(self) -> None:
        response = {"choices": [{"message": {}}]}
        assert OpenRouterClient.extract_content(response) == ""

    def test_extract_content_malformed(self) -> None:
        """Клиент не падает при невалидной структуре ответа."""
        assert OpenRouterClient.extract_content({}) == ""
        assert OpenRouterClient.extract_content({"choices": []}) == ""

    def test_extract_tool_calls(self) -> None:
        response = {
            "choices": [
                {
                    "message": {
                        "tool_calls": [
                            {"id": "call_1", "function": {"name": "test", "arguments": "{}"}}
                        ]
                    }
                }
            ]
        }
        calls = OpenRouterClient.extract_tool_calls(response)
        assert len(calls) == 1
        assert calls[0]["function"]["name"] == "test"

    def test_extract_tool_calls_none(self) -> None:
        response = {"choices": [{"message": {"content": "text"}}]}
        assert OpenRouterClient.extract_tool_calls(response) == []

    def test_extract_tool_calls_malformed(self) -> None:
        """Клиент не падает при отсутствии choices."""
        assert OpenRouterClient.extract_tool_calls({}) == []

    def test_parse_tool_arguments(self) -> None:
        call = {"function": {"arguments": '{"career_goal": "ml"}'}}
        args = OpenRouterClient.parse_tool_arguments(call)
        assert args == {"career_goal": "ml"}

    def test_parse_tool_arguments_invalid_json(self) -> None:
        """Невалидный JSON возвращает пустой dict вместо исключения."""
        call = {"function": {"arguments": "not json"}}
        assert OpenRouterClient.parse_tool_arguments(call) == {}

    def test_parse_tool_arguments_missing_key(self) -> None:
        """Отсутствующие ключи возвращают пустой dict."""
        assert OpenRouterClient.parse_tool_arguments({}) == {}

    def test_validate_response_error_field(self) -> None:
        """Ответ с полем error выбрасывает UpstreamError."""
        from app.exceptions import UpstreamError

        with pytest.raises(UpstreamError, match="модель не найдена"):
            OpenRouterClient._validate_response({"error": {"message": "модель не найдена"}})

    def test_validate_response_no_choices(self) -> None:
        """Ответ без choices выбрасывает UpstreamError."""
        from app.exceptions import UpstreamError

        with pytest.raises(UpstreamError, match="Пустой ответ"):
            OpenRouterClient._validate_response({"choices": []})

    def test_model_switching(self) -> None:
        """Модель переключается через свойство."""
        client = OpenRouterClient(api_key="test", model="model-a")
        assert client.model == "model-a"
        client.model = "model-b"
        assert client.model == "model-b"


# ── Тесты оркестрации ───────────────────────────────────────────────────────


def _make_llm_response(content: str = "", tool_calls: list | None = None) -> dict[str, Any]:
    """Создать мок-ответ LLM."""
    message: dict[str, Any] = {}
    if content:
        message["content"] = content
    if tool_calls:
        message["tool_calls"] = tool_calls
    return {"choices": [{"message": message}]}


def _make_tool_call(fn_name: str, args: dict[str, Any], call_id: str = "call_1") -> dict[str, Any]:
    """Создать мок tool_call."""
    return {
        "id": call_id,
        "function": {"name": fn_name, "arguments": json.dumps(args)},
    }


class TestChatService:
    @pytest.mark.asyncio
    async def test_direct_response(self) -> None:
        """LLM отвечает без function call."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=_make_llm_response("Привет, студент!"))

        service = ChatService(llm_client=mock_client)
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)

        result = await service.process_message("Привет!", profile)
        assert result.reply == "Привет, студент!"

    @pytest.mark.asyncio
    async def test_get_recommendations_flow(self) -> None:
        """LLM вызывает get_recommendations → получает результат → формирует ответ."""
        mock_client = AsyncMock()
        # Первый вызов: LLM решает вызвать функцию
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(tool_calls=[_make_tool_call("get_recommendations", {})]),
                # Второй вызов: LLM формирует ответ по результатам
                _make_llm_response("Рекомендую курс ML!"),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)

        result = await service.process_message("Что мне делать?", profile)
        assert result.reply == "Рекомендую курс ML!"
        assert mock_client.chat.call_count == 2

    @pytest.mark.asyncio
    async def test_recalculate_flow(self) -> None:
        """LLM вызывает recalculate_with_changes с изменением цели."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(
                    tool_calls=[
                        _make_tool_call("recalculate_with_changes", {"career_goal": "backend"})
                    ]
                ),
                _make_llm_response("При смене на бэкенд рекомендую..."),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)

        result = await service.process_message("А если я хочу в бэкенд?", profile)
        assert result.reply == "При смене на бэкенд рекомендую..."

    @pytest.mark.asyncio
    async def test_search_knowledge_flow(self) -> None:
        """LLM вызывает search_knowledge → RAG-заглушка → ответ."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(
                    tool_calls=[_make_tool_call("search_knowledge", {"query": "курс ML"})]
                ),
                _make_llm_response("Курс ML включает..."),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile()

        result = await service.process_message("Расскажи про курс ML", profile)
        assert result.reply == "Курс ML включает..."

    @pytest.mark.asyncio
    async def test_debug_mode(self) -> None:
        """В debug-режиме возвращаются отладочные данные."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(tool_calls=[_make_tool_call("get_recommendations", {})]),
                _make_llm_response("Рекомендации..."),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)

        result = await service.process_message("Что мне делать?", profile, debug=True)
        assert result.debug is not None
        assert len(result.debug.rules_fired) > 0
        assert len(result.debug.tool_calls) == 1
        assert result.debug.tool_calls[0]["function"] == "get_recommendations"

    @pytest.mark.asyncio
    async def test_max_tool_rounds_limit(self) -> None:
        """Не более MAX_TOOL_ROUNDS итераций function calling."""
        mock_client = AsyncMock()
        # LLM бесконечно вызывает функции
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(tool_calls=[_make_tool_call("get_recommendations", {})]),
                _make_llm_response(tool_calls=[_make_tool_call("get_recommendations", {})]),
                _make_llm_response(tool_calls=[_make_tool_call("get_recommendations", {})]),
                # После 3 итераций — финальный вызов без tools
                _make_llm_response("Финальный ответ"),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile()

        result = await service.process_message("тест", profile)
        assert result.reply == "Финальный ответ"
        assert mock_client.chat.call_count == 4  # 3 с tools + 1 без

    @pytest.mark.asyncio
    async def test_history_passed_to_llm(self) -> None:
        """История сообщений передаётся в LLM."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(return_value=_make_llm_response("Ответ"))

        service = ChatService(llm_client=mock_client)
        profile = make_profile()

        history = [
            {"role": "user", "content": "Привет"},
            {"role": "assistant", "content": "Здравствуй!"},
        ]
        await service.process_message("Вопрос", profile, history=history)

        # Проверяем что history вошла в messages
        call_args = mock_client.chat.call_args
        messages = call_args[0][0] if call_args[0] else call_args[1]["messages"]
        roles = [m["role"] for m in messages]
        # system, system (profile), user (history), assistant (history), user (current)
        assert roles.count("user") >= 2
        assert "assistant" in roles

    @pytest.mark.asyncio
    async def test_recalculate_only_allowed_changes(self) -> None:
        """Пересчёт игнорирует недопустимые параметры."""
        mock_client = AsyncMock()
        mock_client.chat = AsyncMock(
            side_effect=[
                _make_llm_response(
                    tool_calls=[
                        _make_tool_call(
                            "recalculate_with_changes",
                            {
                                "career_goal": "backend",
                                "semester": 8,  # недопустимо
                            },
                        )
                    ]
                ),
                _make_llm_response("Результат"),
            ]
        )

        service = ChatService(llm_client=mock_client)
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)

        result = await service.process_message("А если в бэкенд?", profile, debug=True)
        assert result.debug is not None
        # semester не должен попасть в profile_changes
        assert "semester" not in result.debug.profile_changes
        assert result.debug.profile_changes.get("career_goal") == "backend"
