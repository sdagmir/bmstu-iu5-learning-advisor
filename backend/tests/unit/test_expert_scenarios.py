from __future__ import annotations

import pytest

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    TechparkStatus,
    WorkloadPref,
)
from app.expert.engine import PythonRuleEngine
from app.expert.schemas import CKDevStatus, CoverageLevel, StudentProfile
from tests.conftest import make_profile


@pytest.fixture
def engine() -> PythonRuleEngine:
    return PythonRuleEngine()


# ── Сценарий 1: ML-новичок, 4-й семестр ─────────────────────────────────────


class TestScenario1MLBeginner:
    """Сценарий 1 из документации МЭС.

    Вход: X1=ML, X2=4, X3=нет, X4=нормальная, X5=нет, X9=да, X11=низкое
    Ожидание: R1, R25, R29, R35, R40, R42 (6 рекомендаций)
    """

    @pytest.fixture
    def profile(self) -> StudentProfile:
        return make_profile(
            career_goal=CareerGoal.ML,
            semester=4,
            technopark_status=TechparkStatus.NONE,
            workload_pref=WorkloadPref.NORMAL,
            completed_ck_ml=False,
            weak_math=True,
            coverage=CoverageLevel.LOW,
        )

    def test_fires_expected_rules(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        trace, _ = engine.evaluate_with_trace(profile)
        fired = set(trace.fired_rule_numbers)
        assert fired == {1, 25, 29, 35, 40, 42}

    def test_recommendation_count(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        assert len(recs) == 6

    def test_r1_ml_engineer(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r1 = next(r for r in recs if r.rule_id == "R1")
        assert r1.title == "Инженер машинного обучения"
        assert r1.priority == RecommendationPriority.HIGH
        assert r1.category == RecommendationCategory.CK_COURSE

    def test_r25_technopark_ml(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r25 = next(r for r in recs if r.rule_id == "R25")
        assert r25.category == RecommendationCategory.TECHNOPARK

    def test_r29_focus_db(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r29 = next(r for r in recs if r.rule_id == "R29")
        assert r29.category == RecommendationCategory.FOCUS
        assert "аналитические запросы" in r29.title

    def test_r42_math_warning(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r42 = next(r for r in recs if r.rule_id == "R42")
        assert r42.category == RecommendationCategory.WARNING
        assert r42.priority == RecommendationPriority.HIGH


# ── Сценарий 2: Бэкенд, 6-й семестр, в Технопарке ──────────────────────────


class TestScenario2BackendSenior:
    """Сценарий 2 из документации МЭС.

    Вход: X1=бэкенд, X2=6, X3=бэкенд, X4=нормальная, X6=частично, X11=среднее
    Ожидание: R6, R38, R40, R50 (4 рекомендации)
    """

    @pytest.fixture
    def profile(self) -> StudentProfile:
        return make_profile(
            career_goal=CareerGoal.BACKEND,
            semester=6,
            technopark_status=TechparkStatus.BACKEND,
            workload_pref=WorkloadPref.NORMAL,
            ck_dev_status=CKDevStatus.PARTIAL,
            coverage=CoverageLevel.MEDIUM,
        )

    def test_fires_expected_rules(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        trace, _ = engine.evaluate_with_trace(profile)
        fired = set(trace.fired_rule_numbers)
        assert fired == {6, 38, 40, 50}

    def test_recommendation_count(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        assert len(recs) == 4

    def test_r6_system_analyst(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r6 = next(r for r in recs if r.rule_id == "R6")
        assert r6.title == "Системный аналитик"

    def test_r50_synergy(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r50 = next(r for r in recs if r.rule_id == "R50")
        assert r50.category == RecommendationCategory.STRATEGY
        assert "синергия" in r50.reasoning.lower() or "совпадает" in r50.reasoning.lower()


# ── Сценарий 3: Не определился, 2-й семестр ─────────────────────────────────


class TestScenario3Undecided:
    """Сценарий 3 из документации МЭС.

    Вход: X1=не_определился, X2=2, X3=нет, X4=нормальная
    Ожидание: R20, R47 (2 рекомендации)
    """

    @pytest.fixture
    def profile(self) -> StudentProfile:
        return make_profile(
            career_goal=CareerGoal.UNDECIDED,
            semester=2,
            technopark_status=TechparkStatus.NONE,
            workload_pref=WorkloadPref.NORMAL,
        )

    def test_fires_expected_rules(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        trace, _ = engine.evaluate_with_trace(profile)
        fired = set(trace.fired_rule_numbers)
        assert fired == {20, 47}

    def test_recommendation_count(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        assert len(recs) == 2

    def test_r20_digital_skills(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r20 = next(r for r in recs if r.rule_id == "R20")
        assert r20.title == "Цифровые навыки"
        assert r20.priority == RecommendationPriority.HIGH

    def test_r47_strategy(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r47 = next(r for r in recs if r.rule_id == "R47")
        assert r47.category == RecommendationCategory.STRATEGY


# ── Сценарий 4: Кибербез, 7-й семестр, низкое покрытие ──────────────────────


class TestScenario4CyberLate:
    """Сценарий 4 из документации МЭС.

    Вход: X1=кибербез, X2=7, X3=нет, X4=интенсивная, X7=нет, X11=низкое
    Ожидание: R9, R27, R40, R41, R48 (5 рекомендаций)
    Примечание: R41 тоже срабатывает, т.к. semester=7 активирует диверсификацию курсовых.
    В исходной таблице МЭС указан только R40, но R41 корректен по условию (X2=7).
    """

    @pytest.fixture
    def profile(self) -> StudentProfile:
        return make_profile(
            career_goal=CareerGoal.CYBERSECURITY,
            semester=7,
            technopark_status=TechparkStatus.NONE,
            workload_pref=WorkloadPref.INTENSIVE,
            completed_ck_security=False,
            coverage=CoverageLevel.LOW,
        )

    def test_fires_expected_rules(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        trace, _ = engine.evaluate_with_trace(profile)
        fired = set(trace.fired_rule_numbers)
        assert fired == {9, 27, 40, 41, 48}

    def test_recommendation_count(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        assert len(recs) == 5

    def test_r9_cybersecurity(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r9 = next(r for r in recs if r.rule_id == "R9")
        assert r9.title == "Обеспечение информационной безопасности"
        assert r9.priority == RecommendationPriority.HIGH

    def test_r27_tp_too_late(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r27 = next(r for r in recs if r.rule_id == "R27")
        assert r27.category == RecommendationCategory.TECHNOPARK
        assert "не рекомендуется" in r27.title.lower()

    def test_r48_urgent_strategy(self, engine: PythonRuleEngine, profile: StudentProfile) -> None:
        recs = engine.evaluate(profile)
        r48 = next(r for r in recs if r.rule_id == "R48")
        assert r48.category == RecommendationCategory.STRATEGY
        assert r48.priority == RecommendationPriority.HIGH
