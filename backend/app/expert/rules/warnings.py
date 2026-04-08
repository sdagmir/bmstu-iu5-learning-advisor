from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
    TechparkStatus,
    WorkloadPref,
)
from app.expert.registry import rule
from app.expert.schemas import Recommendation, StudentProfile

# ── Группа 6: Предупреждения (5 правил, R42-R46) ────────────────────────────


@rule(
    number=42,
    group=RuleGroup.WARNINGS,
    name="Предупреждение: математика для ML",
    output_param=RecommendationCategory.WARNING,
    input_params=("X1", "X9"),
    priority=RecommendationPriority.HIGH,
)
def r42_warn_math_ml(profile: StudentProfile) -> Recommendation | None:
    """R42: X1=ML И X9=да → Слабая база по математике для ML"""
    if profile.career_goal == CareerGoal.ML and profile.weak_math:
        return Recommendation(
            rule_id="R42",
            category=RecommendationCategory.WARNING,
            title="Слабая база по математике для программы ML",
            priority=RecommendationPriority.HIGH,
            reasoning="Программа ML опирается на линейную алгебру и теорию вероятностей",
            competency_gap="linear_algebra",
        )
    return None


@rule(
    number=43,
    group=RuleGroup.WARNINGS,
    name="Предупреждение: математика для аналитики",
    output_param=RecommendationCategory.WARNING,
    input_params=("X1", "X9"),
    priority=RecommendationPriority.HIGH,
)
def r43_warn_math_analytics(profile: StudentProfile) -> Recommendation | None:
    """R43: X1=аналитика И X9=да → Слабая база по математике для аналитики"""
    if profile.career_goal == CareerGoal.ANALYTICS and profile.weak_math:
        return Recommendation(
            rule_id="R43",
            category=RecommendationCategory.WARNING,
            title="Слабая база по математике для аналитики",
            priority=RecommendationPriority.HIGH,
            reasoning="Аналитика данных требует статистику и теорию вероятностей",
            competency_gap="statistics",
        )
    return None


@rule(
    number=44,
    group=RuleGroup.WARNINGS,
    name="Предупреждение: программирование",
    output_param=RecommendationCategory.WARNING,
    input_params=("X1", "X10"),
    priority=RecommendationPriority.HIGH,
)
def r44_warn_programming(profile: StudentProfile) -> Recommendation | None:
    """R44: X1∈{ML, бэкенд, DevOps} И X10=да → Слабая база по программированию"""
    if (
        profile.career_goal
        in {
            CareerGoal.ML,
            CareerGoal.BACKEND,
            CareerGoal.DEVOPS,
        }
        and profile.weak_programming
    ):
        return Recommendation(
            rule_id="R44",
            category=RecommendationCategory.WARNING,
            title="Слабая база по программированию для выбранного направления",
            priority=RecommendationPriority.HIGH,
            reasoning="Выбранное направление требует уверенного владения программированием",
            competency_gap="python",
        )
    return None


@rule(
    number=45,
    group=RuleGroup.WARNINGS,
    name="Предупреждение: нагрузка ТП",
    output_param=RecommendationCategory.WARNING,
    input_params=("X4", "X3"),
    priority=RecommendationPriority.MEDIUM,
)
def r45_warn_tp_overload(profile: StudentProfile) -> Recommendation | None:
    """R45: X4=лёгкая И X3≠нет → Технопарк + ЦК при лёгкой нагрузке — риск"""
    if (
        profile.workload_pref == WorkloadPref.LIGHT
        and profile.technopark_status != TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R45",
            category=RecommendationCategory.WARNING,
            title="Риск перегруза при лёгкой нагрузке",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Технопарк + программы ЦК при желании лёгкой нагрузки — риск перегруза",
        )
    return None


@rule(
    number=46,
    group=RuleGroup.WARNINGS,
    name="Предупреждение: интенсив на ранних",
    output_param=RecommendationCategory.WARNING,
    input_params=("X4", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r46_warn_early_intensive(profile: StudentProfile) -> Recommendation | None:
    """R46: X4=интенсивная И X2∈{1,2} → Интенсивная нагрузка на ранних семестрах рискованна"""
    if profile.workload_pref == WorkloadPref.INTENSIVE and profile.semester in {1, 2}:
        return Recommendation(
            rule_id="R46",
            category=RecommendationCategory.WARNING,
            title="Интенсивная нагрузка на ранних семестрах рискованна",
            priority=RecommendationPriority.MEDIUM,
            reasoning="На 1-2 семестрах важно адаптироваться, не перегружаться сразу",
        )
    return None
