from __future__ import annotations

from app.db.models import (
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
    TechparkStatus,
)
from app.expert.helpers import GOAL_TO_OPTIMAL_TECHNOPARK
from app.expert.registry import rule
from app.expert.schemas import CoverageLevel, Recommendation, StudentProfile

# ── Группа 7: Стратегическое планирование (4 правила, R47-R50) ───────────────


@rule(
    number=47,
    group=RuleGroup.STRATEGY,
    name="Стратегия: ранний семестр",
    output_param=RecommendationCategory.STRATEGY,
    input_params=("X2",),
    priority=RecommendationPriority.MEDIUM,
)
def r47_strategy_early(profile: StudentProfile) -> Recommendation | None:
    """R47: X2∈{1,2} → Фокус на базу: математика и программирование"""
    if profile.semester in {1, 2}:
        return Recommendation(
            rule_id="R47",
            category=RecommendationCategory.STRATEGY,
            title="Фокус на базу: математика и программирование",
            priority=RecommendationPriority.MEDIUM,
            reasoning="На ранних семестрах приоритет — фундаментальные дисциплины",
        )
    return None


@rule(
    number=48,
    group=RuleGroup.STRATEGY,
    name="Стратегия: мало времени, низкое покрытие",
    output_param=RecommendationCategory.STRATEGY,
    input_params=("X2", "X11"),
    priority=RecommendationPriority.HIGH,
)
def r48_strategy_urgent(profile: StudentProfile) -> Recommendation | None:
    """R48: X2≥6 И X11=низкое → Интенсивный план по целевым пробелам"""
    if profile.semester >= 6 and profile.coverage == CoverageLevel.LOW:
        return Recommendation(
            rule_id="R48",
            category=RecommendationCategory.STRATEGY,
            title="Интенсивный план: максимум программ ЦК по целевым пробелам",
            priority=RecommendationPriority.HIGH,
            reasoning="Мало семестров осталось при низком покрытии — нужен интенсивный план",
        )
    return None


@rule(
    number=49,
    group=RuleGroup.STRATEGY,
    name="Стратегия: высокое покрытие",
    output_param=RecommendationCategory.STRATEGY,
    input_params=("X11",),
    priority=RecommendationPriority.MEDIUM,
)
def r49_strategy_deep(profile: StudentProfile) -> Recommendation | None:
    """R49: X11=высокое → Профиль почти собран, углубляться в специализацию"""
    if profile.coverage == CoverageLevel.HIGH:
        return Recommendation(
            rule_id="R49",
            category=RecommendationCategory.STRATEGY,
            title="Профиль почти собран — углубляться в специализацию",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Покрытие целевого профиля высокое, пора углубляться, а не расширяться",
        )
    return None


@rule(
    number=50,
    group=RuleGroup.STRATEGY,
    name="Стратегия: синергия",
    output_param=RecommendationCategory.STRATEGY,
    input_params=("X1", "X3"),
    priority=RecommendationPriority.MEDIUM,
)
def r50_strategy_synergy(profile: StudentProfile) -> Recommendation | None:
    """R50: X3 совпадает с оптимальным для X1 → Удачная комбинация"""
    if profile.technopark_status == TechparkStatus.NONE:
        return None
    optimal = GOAL_TO_OPTIMAL_TECHNOPARK.get(profile.career_goal)
    if optimal is not None and profile.technopark_status == optimal:
        return Recommendation(
            rule_id="R50",
            category=RecommendationCategory.STRATEGY,
            title="Удачная комбинация: Технопарк + ЦК + цель в одном направлении",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Направление Технопарка совпадает с карьерной целью — синергия",
        )
    return None
