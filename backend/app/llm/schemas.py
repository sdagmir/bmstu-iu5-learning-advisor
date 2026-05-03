from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Одно сообщение в истории диалога."""

    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    """Запрос на обработку сообщения в чате."""

    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Ответ чата."""

    reply: str
    debug: DebugInfo | None = None


class DebugInfo(BaseModel):
    """Отладочные данные для тестового чата администратора."""

    rules_fired: list[str] = Field(default_factory=list)
    rag_chunks: list[str] = Field(default_factory=list)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    profile_changes: dict[str, Any] = Field(default_factory=dict)
