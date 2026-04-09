from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser, DbSession
from app.expert.schemas import Recommendation, StudentProfile
from app.expert.service import expert_service
from app.users.profile_builder import build_student_profile

router = APIRouter()


@router.get("/my-recommendations", response_model=list[Recommendation])
async def my_recommendations(user: CurrentUser, db: DbSession) -> list[Recommendation]:
    """Рекомендации для текущего пользователя (профиль вычисляется автоматически)."""
    profile = await build_student_profile(user, db)
    return expert_service.get_recommendations(profile)


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
