"""Роутер чата — студенческий и debug для админа."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser, DbSession
from app.expert.schemas import StudentProfile
from app.llm.schemas import ChatRequest, ChatResponse, DebugInfo
from app.llm.service import chat_service

router = APIRouter()


async def _build_profile_from_user(user: Any) -> StudentProfile:
    """Построить StudentProfile из данных пользователя."""
    from app.db.models import CareerGoal, TechparkStatus, WorkloadPref
    from app.expert.schemas import CKCategoryCount, CKDevStatus, CoverageLevel

    return StudentProfile(
        user_id=user.id,
        semester=user.semester or 1,
        career_goal=CareerGoal(user.career_goal) if user.career_goal else CareerGoal.UNDECIDED,
        technopark_status=(
            TechparkStatus(user.technopark_status)
            if user.technopark_status
            else TechparkStatus.NONE
        ),
        workload_pref=(
            WorkloadPref(user.workload_pref) if user.workload_pref else WorkloadPref.NORMAL
        ),
        # TODO: вычислять из student_completed_ck и student_weak_subjects
        completed_ck_ml=False,
        ck_dev_status=CKDevStatus.NO,
        completed_ck_security=False,
        completed_ck_testing=False,
        weak_math=False,
        weak_programming=False,
        coverage=CoverageLevel.LOW,
        ck_count_in_category=CKCategoryCount.FEW,
    )


@router.post("/message", response_model=ChatResponse)
async def send_message(body: ChatRequest, user: CurrentUser, db: DbSession) -> ChatResponse:
    """Отправка сообщения в чат (студент)."""
    profile = await _build_profile_from_user(user)
    history = [{"role": m.role, "content": m.content} for m in body.history]

    result = await chat_service.process_message(
        message=body.message, profile=profile, history=history
    )
    return ChatResponse(reply=result.reply)


@router.post("/message/debug", response_model=ChatResponse)
async def send_message_debug(
    body: ChatRequest, admin: CurrentAdmin, db: DbSession
) -> ChatResponse:
    """Отправка сообщения в debug-чат (админ). Возвращает отладочные данные."""
    profile = await _build_profile_from_user(admin)
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
