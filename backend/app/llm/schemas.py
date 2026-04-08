from __future__ import annotations

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system" — роль в диалоге
    content: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    debug: DebugInfo | None = None


class DebugInfo(BaseModel):
    """Отладочные данные для тестового чата администратора."""

    rules_fired: list[str] = []
    rag_chunks: list[str] = []
    llm_prompt: str = ""
