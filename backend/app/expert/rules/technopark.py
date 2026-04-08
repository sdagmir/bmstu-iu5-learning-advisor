from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
    TechparkStatus,
)
from app.expert.helpers import GOAL_TO_OPTIMAL_TECHNOPARK
from app.expert.registry import rule
from app.expert.schemas import Recommendation, StudentProfile

# ── Группа 3: Технопарк (8 правил, R23-R28, R51-R52) ────────────────────────


@rule(
    number=23,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: бэкенд",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r23_tp_backend(profile: StudentProfile) -> Recommendation | None:
    """R23: X1=бэкенд И X2∈[2..4] И X3=нет → ТП бэкенд"""
    if (
        profile.career_goal == CareerGoal.BACKEND
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R23",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «бэкенд-разработка»",
            priority=RecommendationPriority.HIGH,
            reasoning="Оптимальное время для вступления, направление совпадает с целью",
        )
    return None


@rule(
    number=24,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: фронтенд",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r24_tp_frontend(profile: StudentProfile) -> Recommendation | None:
    """R24: X1=фронтенд И X2∈[2..4] И X3=нет → ТП фронтенд"""
    if (
        profile.career_goal == CareerGoal.FRONTEND
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R24",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «фронтенд-разработка»",
            priority=RecommendationPriority.HIGH,
            reasoning="Оптимальное время для вступления, направление совпадает с целью",
        )
    return None


@rule(
    number=25,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: ML",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r25_tp_ml(profile: StudentProfile) -> Recommendation | None:
    """R25: X1=ML И X2∈[2..4] И X3=нет → ТП ML"""
    if (
        profile.career_goal == CareerGoal.ML
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R25",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «машинное обучение»",
            priority=RecommendationPriority.HIGH,
            reasoning="Оптимальное время для вступления, направление совпадает с целью",
        )
    return None


@rule(
    number=26,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: мобильная",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r26_tp_mobile(profile: StudentProfile) -> Recommendation | None:
    """R26: X1=мобильная И X2∈[2..4] И X3=нет → ТП мобильная"""
    if (
        profile.career_goal == CareerGoal.MOBILE
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R26",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «мобильная разработка»",
            priority=RecommendationPriority.HIGH,
            reasoning="Оптимальное время для вступления, направление совпадает с целью",
        )
    return None


@rule(
    number=27,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: поздно",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X2", "X3"),
    priority=RecommendationPriority.MEDIUM,
)
def r27_tp_too_late(profile: StudentProfile) -> Recommendation | None:
    """R27: X2≥6 И X3=нет → Не рекомендовать Технопарк (поздно)"""
    if profile.semester >= 6 and profile.technopark_status == TechparkStatus.NONE:
        return Recommendation(
            rule_id="R27",
            category=RecommendationCategory.TECHNOPARK,
            title="Технопарк не рекомендуется",
            priority=RecommendationPriority.MEDIUM,
            reasoning="На 6+ семестре начинать Технопарк поздно — лучше сосредоточиться на ЦК",
        )
    return None


@rule(
    number=28,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: несоответствие",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X3"),
    priority=RecommendationPriority.MEDIUM,
)
def r28_tp_mismatch(profile: StudentProfile) -> Recommendation | None:
    """R28: X3≠нет И X3≠оптимальное_для(X1) → Предупреждение о несоответствии"""
    if profile.technopark_status == TechparkStatus.NONE:
        return None
    optimal = GOAL_TO_OPTIMAL_TECHNOPARK.get(profile.career_goal)
    if optimal is None or profile.technopark_status == optimal:
        return None
    return Recommendation(
        rule_id="R28",
        category=RecommendationCategory.TECHNOPARK,
        title="Несоответствие направления Технопарка и карьерной цели",
        priority=RecommendationPriority.MEDIUM,
        reasoning=(
            f"Направление ТП «{profile.technopark_status}» "
            f"не соответствует цели «{profile.career_goal}»"
        ),
    )


@rule(
    number=51,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: DevOps → бэкенд",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r51_tp_devops(profile: StudentProfile) -> Recommendation | None:
    """R51: X1=DevOps И X2∈[2..4] И X3=нет → ТП бэкенд (ближайшее к DevOps)"""
    if (
        profile.career_goal == CareerGoal.DEVOPS
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R51",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «бэкенд-разработка»",
            priority=RecommendationPriority.HIGH,
            reasoning="Направление бэкенд — ближайшее к DevOps в Технопарке",
        )
    return None


@rule(
    number=52,
    group=RuleGroup.TECHNOPARK,
    name="Технопарк: аналитика → ML",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1", "X2", "X3"),
    priority=RecommendationPriority.HIGH,
)
def r52_tp_analytics(profile: StudentProfile) -> Recommendation | None:
    """R52: X1=аналитика И X2∈[2..4] И X3=нет → ТП ML (ближайшее к аналитике)"""
    if (
        profile.career_goal == CareerGoal.ANALYTICS
        and 2 <= profile.semester <= 4
        and profile.technopark_status == TechparkStatus.NONE
    ):
        return Recommendation(
            rule_id="R52",
            category=RecommendationCategory.TECHNOPARK,
            title="Вступить в Технопарк, направление «машинное обучение»",
            priority=RecommendationPriority.HIGH,
            reasoning="Направление ML — ближайшее к аналитике данных в Технопарке",
        )
    return None
