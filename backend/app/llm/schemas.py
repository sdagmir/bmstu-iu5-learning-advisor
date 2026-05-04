from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

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


# ── Трейсы LLM-запросов (admin) ────────────────────────────────────────────

TraceEndpoint = Literal["message", "message/debug"]
TraceStatus = Literal["ok", "error", "timeout"]


class TraceSummary(BaseModel):
    """Запись для списка `/admin/traces` (без полного тела запроса)."""

    id: uuid.UUID
    created_at: datetime
    user_email: str
    endpoint: TraceEndpoint
    latency_ms: int
    status: TraceStatus
    rules_fired_count: int
    request_preview: str  # первые 80 символов request_message


class TraceDetail(BaseModel):
    """Полная запись `/admin/traces/{id}` с request, response и debug."""

    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID
    user_email: str
    endpoint: TraceEndpoint
    request_message: str
    response_text: str
    debug: DebugInfo | None = None
    latency_ms: int
    status: TraceStatus
    model_name: str | None = None
