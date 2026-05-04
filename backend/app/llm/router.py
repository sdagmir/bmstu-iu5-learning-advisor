"""Роутер чата — студенческий и debug для админа."""

from __future__ import annotations

import time

from fastapi import APIRouter, BackgroundTasks

from app.db.database import async_session_factory
from app.dependencies import CurrentAdmin, CurrentUser
from app.llm.schemas import ChatRequest, ChatResponse, DebugInfo
from app.llm.service import chat_service, write_trace
from app.users.profile_builder import build_student_profile

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    body: ChatRequest, user: CurrentUser, background: BackgroundTasks
) -> ChatResponse:
    """Отправка сообщения в чат (студент)."""
    # Короткая сессия только под построение профиля; LLM-вызов идёт без DB connection
    async with async_session_factory() as db:
        profile = await build_student_profile(user, db)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    started = time.monotonic()
    try:
        result = await chat_service.process_message(
            message=body.message, profile=profile, history=history
        )
    except BaseException:
        latency_ms = int((time.monotonic() - started) * 1000)
        background.add_task(
            write_trace,
            user_id=user.id,
            endpoint="message",
            request_message=body.message,
            response_text="",
            debug=None,
            latency_ms=latency_ms,
            status="error",
        )
        raise

    latency_ms = int((time.monotonic() - started) * 1000)
    background.add_task(
        write_trace,
        user_id=user.id,
        endpoint="message",
        request_message=body.message,
        response_text=result.reply,
        debug=None,
        latency_ms=latency_ms,
        status="ok",
    )
    return ChatResponse(reply=result.reply)


@router.post("/message/debug", response_model=ChatResponse)
async def send_message_debug(
    body: ChatRequest, admin: CurrentAdmin, background: BackgroundTasks
) -> ChatResponse:
    """Отправка сообщения в debug-чат (админ). Возвращает отладочные данные."""
    async with async_session_factory() as db:
        profile = await build_student_profile(admin, db)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    started = time.monotonic()
    try:
        result = await chat_service.process_message(
            message=body.message, profile=profile, history=history, debug=True
        )
    except BaseException:
        latency_ms = int((time.monotonic() - started) * 1000)
        background.add_task(
            write_trace,
            user_id=admin.id,
            endpoint="message/debug",
            request_message=body.message,
            response_text="",
            debug=None,
            latency_ms=latency_ms,
            status="error",
        )
        raise

    latency_ms = int((time.monotonic() - started) * 1000)
    background.add_task(
        write_trace,
        user_id=admin.id,
        endpoint="message/debug",
        request_message=body.message,
        response_text=result.reply,
        debug=result.debug,
        latency_ms=latency_ms,
        status="ok",
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
