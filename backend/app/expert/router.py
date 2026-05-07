from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser, DbSession, PageLimit, PageOffset
from app.expert.schemas import Recommendation, RecommendationSnapshot, StudentProfile
from app.expert.service import (
    enrich_with_courses,
    expert_service,
    increment_rule_triggers,
    list_recommendation_history,
)
from app.users.profile_builder import build_student_profile

router = APIRouter()


@router.get("/my-recommendations", response_model=list[Recommendation])
async def my_recommendations(user: CurrentUser, db: DbSession) -> list[Recommendation]:
    """Рекомендации для текущего пользователя (профиль вычисляется автоматически).

    Это production-путь — счётчик trigger_count у сработавших правил
    инкрементируется. /evaluate и preview-вызовы счётчик не трогают.
    """
    profile = await build_student_profile(user, db)
    trace, recommendations = expert_service.get_recommendations_debug(profile)
    await increment_rule_triggers(trace.fired_rule_numbers, db)
    return await enrich_with_courses(recommendations, db)


@router.get("/recommendations/history", response_model=list[RecommendationSnapshot])
async def recommendations_history(
    user: CurrentUser,
    db: DbSession,
    offset: PageOffset = 0,
    limit: PageLimit = 50,
) -> list[RecommendationSnapshot]:
    """Лента прошлых снапшотов рекомендаций (создаются при изменении X1–X4)."""
    return await list_recommendation_history(user.id, db, offset=offset, limit=limit)


@router.post("/evaluate", response_model=list[Recommendation])
async def evaluate(profile: StudentProfile, user: CurrentUser) -> list[Recommendation]:
    """Рекомендации по произвольному профилю (для тестирования what-if)."""
    return expert_service.get_recommendations(profile)


@router.post("/evaluate/debug")
async def evaluate_debug(profile: StudentProfile, admin: CurrentAdmin) -> dict[str, Any]:
    """Рекомендации с трассировкой (только для админа)."""
    trace, recommendations = expert_service.get_recommendations_debug(profile)
    return {
        "recommendations": [r.model_dump() for r in recommendations],
        "trace": {
            "profile_snapshot": trace.profile_snapshot,
            "total_checked": trace.total_checked,
            "total_fired": trace.total_fired,
            "fired_rule_ids": trace.rules_fired_ids,
            "entries": [
                {
                    "rule": f"R{e.rule_number}",
                    "name": e.rule_name,
                    "group": e.group,
                    "fired": e.fired,
                    "skipped_reason": e.skipped_reason,
                }
                for e in trace.entries
            ],
        },
    }
