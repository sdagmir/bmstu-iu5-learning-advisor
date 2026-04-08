from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
)
from app.expert.schemas import CKDevStatus, CoverageLevel, Recommendation
from tests.conftest import make_profile


class TestStudentProfile:
    def test_create_ml_student(self) -> None:
        profile = make_profile(
            career_goal=CareerGoal.ML,
            semester=4,
            completed_ck_ml=False,
            weak_math=True,
        )
        assert profile.career_goal == CareerGoal.ML
        assert profile.semester == 4
        assert profile.weak_math is True
        assert profile.ck_dev_status == CKDevStatus.NO

    def test_create_undecided_student(self) -> None:
        profile = make_profile(career_goal=CareerGoal.UNDECIDED, semester=2)
        assert profile.career_goal == CareerGoal.UNDECIDED
        assert profile.completed_ck_ml is False
        assert profile.coverage == CoverageLevel.LOW

    def test_ck_dev_status_values(self) -> None:
        for status in CKDevStatus:
            profile = make_profile(ck_dev_status=status)
            assert profile.ck_dev_status == status


class TestRecommendation:
    def test_create_recommendation(self) -> None:
        rec = Recommendation(
            rule_id="R1",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер машинного обучения",
            priority=RecommendationPriority.HIGH,
            reasoning="Закрывает пробел ml_basics",
            competency_gap="ml_basics",
        )
        assert rec.rule_id == "R1"
        assert rec.priority == RecommendationPriority.HIGH
        assert rec.competency_gap == "ml_basics"

    def test_recommendation_without_gap(self) -> None:
        rec = Recommendation(
            rule_id="R47",
            category=RecommendationCategory.STRATEGY,
            title="Фокус на базу",
            priority=RecommendationPriority.MEDIUM,
            reasoning="На ранних семестрах — математика и программирование",
        )
        assert rec.competency_gap is None
