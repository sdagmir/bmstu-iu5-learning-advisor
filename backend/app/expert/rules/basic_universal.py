from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
)
from app.expert.registry import rule
from app.expert.schemas import CKCategoryCount, Recommendation, StudentProfile

# ── Группа 2: Базовые и универсальные программы (3 правила, R20-R22) ─────────


@rule(
    number=20,
    group=RuleGroup.BASIC_UNIVERSAL,
    name="Не определился: цифровые навыки",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.HIGH,
)
def r20_undecided_digital(profile: StudentProfile) -> Recommendation | None:
    """R20: X1=не_определился И X2≤3 → Цифровые навыки (высокий)"""
    if profile.career_goal == CareerGoal.UNDECIDED and profile.semester <= 3:
        return Recommendation(
            rule_id="R20",
            category=RecommendationCategory.CK_COURSE,
            title="Цифровые навыки",
            priority=RecommendationPriority.HIGH,
            reasoning="Универсальная программа для ранних семестров, пока цель не определена",
            competency_gap="python",
        )
    return None


@rule(
    number=21,
    group=RuleGroup.BASIC_UNIVERSAL,
    name="Не определился: low-code",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r21_undecided_lowcode(profile: StudentProfile) -> Recommendation | None:
    """R21: X1=не_определился И X2≥4 → Low-code разработка (средний)"""
    if profile.career_goal == CareerGoal.UNDECIDED and profile.semester >= 4:
        return Recommendation(
            rule_id="R21",
            category=RecommendationCategory.CK_COURSE,
            title="Low-code разработка",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Практичная программа, полезна для любого направления",
            competency_gap="api_design",
        )
    return None


@rule(
    number=22,
    group=RuleGroup.BASIC_UNIVERSAL,
    name="Диверсификация",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X12",),
    priority=RecommendationPriority.LOW,
)
def r22_diversification(profile: StudentProfile) -> Recommendation | None:
    """R22: X12=много → Рекомендовать программу из другой категории (низкий)"""
    if profile.ck_count_in_category == CKCategoryCount.MANY:
        return Recommendation(
            rule_id="R22",
            category=RecommendationCategory.CK_COURSE,
            title="Программа из другой категории ЦК",
            priority=RecommendationPriority.LOW,
            reasoning="Много программ одной категории — стоит расширить кругозор",
        )
    return None
