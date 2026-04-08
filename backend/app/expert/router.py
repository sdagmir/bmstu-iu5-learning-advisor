from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.dependencies import CurrentAdmin, CurrentUser
from app.expert.schemas import Recommendation, StudentProfile
from app.expert.service import expert_service

router = APIRouter()


@router.post("/evaluate", response_model=list[Recommendation])
async def evaluate(profile: StudentProfile, user: CurrentUser) -> list[Recommendation]:
    return expert_service.get_recommendations(profile)


@router.post("/evaluate/debug")
async def evaluate_debug(profile: StudentProfile, admin: CurrentAdmin) -> dict[str, Any]:
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
