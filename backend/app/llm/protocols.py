from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from app.llm.schemas import ChatMessage


class LLMClient(Protocol):
    """Интерфейс взаимодействия с LLM API.

    Реализации:
    - OpenRouterClient (app.llm.client) — OpenRouter API (OpenAI-совместимый)
    """

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.3,
    ) -> dict[str, Any]:
        """Нестриминговое завершение чата. Возвращает полный словарь ответа."""
        ...

    async def stream(
        self,
        messages: list[ChatMessage],
        *,
        temperature: float = 0.3,
    ) -> AsyncIterator[str]:
        """Стриминговое завершение чата. Генерирует фрагменты контента."""
        ...
