from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatMessage(BaseModel):
    """Одно сообщение в истории диалога."""

    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Запрос на обработку сообщения в чате."""

    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    """Ответ чата."""

    reply: str
    debug: DebugInfo | None = None


class DebugInfo(BaseModel):
    """Отладочные данные для тестового чата администратора."""

    rules_fired: list[str] = []
    rag_chunks: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    profile_changes: dict[str, Any] = {}
