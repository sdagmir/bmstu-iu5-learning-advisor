from __future__ import annotations

from app.db.models import (
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
)
from app.expert.helpers import GOAL_TO_COURSEWORK_AREA
from app.expert.registry import rule
from app.expert.schemas import Recommendation, StudentProfile

# ── Группа 5: Темы курсовых работ (2 правила, R40-R41) ──────────────────────


@rule(
    number=40,
    group=RuleGroup.COURSEWORK,
    name="Курсовая по цели",
    output_param=RecommendationCategory.COURSEWORK,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r40_coursework_by_goal(profile: StudentProfile) -> Recommendation | None:
    """R40: X2∈{4,5,6,7} → Рекомендовать тему курсовой в области X1"""
    if profile.semester in {4, 5, 6, 7}:
        area = GOAL_TO_COURSEWORK_AREA.get(profile.career_goal, "разработки ПО")
        return Recommendation(
            rule_id="R40",
            category=RecommendationCategory.COURSEWORK,
            title=f"Тема курсовой в области {area}",
            priority=RecommendationPriority.MEDIUM,
            reasoning=f"Курсовая в области {area} укрепит портфолио по целевому направлению",
        )
    return None


@rule(
    number=41,
    group=RuleGroup.COURSEWORK,
    name="Курсовая: диверсификация",
    output_param=RecommendationCategory.COURSEWORK,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.LOW,
)
def r41_coursework_diversify(profile: StudentProfile) -> Recommendation | None:
    """R41: X2=7 → Предложить смежную область для расширения портфолио"""
    if profile.semester == 7:
        return Recommendation(
            rule_id="R41",
            category=RecommendationCategory.COURSEWORK,
            title="Курсовая в смежной области для расширения портфолио",
            priority=RecommendationPriority.LOW,
            reasoning="К 7-му семестру основные курсовые уже были — стоит расширить спектр",
        )
    return None
