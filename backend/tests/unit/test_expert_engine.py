from __future__ import annotations

from app.db.models import CareerGoal, RecommendationPriority, RuleGroup, TechparkStatus
from app.expert.engine import PythonRuleEngine
from app.expert.registry import registry
from app.expert.schemas import CoverageLevel
from tests.conftest import make_profile


class TestRuleRegistry:
    def test_all_52_rules_registered(self) -> None:
        import app.expert.rules  # noqa: F401

        assert registry.count == 52

    def test_no_duplicate_numbers(self) -> None:
        numbers = [r.number for r in registry.get_all()]
        assert len(numbers) == len(set(numbers))

    def test_all_groups_present(self) -> None:
        groups = {r.group for r in registry.get_all()}
        expected = {g.value for g in RuleGroup}
        assert groups == expected

    def test_deterministic_order(self) -> None:
        first = [r.number for r in registry.get_all()]
        second = [r.number for r in registry.get_all()]
        assert first == second

    def test_group_ordering(self) -> None:
        rules = registry.get_all()
        groups_seen: list[str] = []
        for r in rules:
            if not groups_seen or groups_seen[-1] != r.group:
                groups_seen.append(r.group)
        expected_order = [
            "ck_programs",
            "basic_universal",
            "technopark",
            "discipline_focus",
            "coursework",
            "warnings",
            "strategy",
        ]
        assert groups_seen == expected_order


class TestPythonRuleEngine:
    def test_satisfies_protocol(self) -> None:
        engine = PythonRuleEngine()
        assert hasattr(engine, "evaluate")
        assert callable(engine.evaluate)

    def test_rule_count(self) -> None:
        engine = PythonRuleEngine()
        assert engine.rule_count == 52

    def test_deterministic_output(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)
        r1 = engine.evaluate(profile)
        r2 = engine.evaluate(profile)
        assert [r.rule_id for r in r1] == [r.rule_id for r in r2]

    def test_trace_covers_all_rules(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile()
        trace, _ = engine.evaluate_with_trace(profile)
        assert trace.total_checked == 52

    def test_trace_profile_snapshot(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(career_goal=CareerGoal.BACKEND, semester=3)
        trace, _ = engine.evaluate_with_trace(profile)
        assert trace.profile_snapshot["career_goal"] == "backend"
        assert trace.profile_snapshot["semester"] == 3

    def test_undecided_student_gets_recommendations(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(career_goal=CareerGoal.UNDECIDED, semester=2)
        recs = engine.evaluate(profile)
        assert len(recs) > 0

    def test_empty_result_possible(self) -> None:
        """Узкоспециальный профиль может совпасть с малым числом правил."""
        engine = PythonRuleEngine()
        profile = make_profile(
            career_goal=CareerGoal.QA,
            semester=3,
            completed_ck_testing=True,
            coverage=CoverageLevel.MEDIUM,
        )
        recs = engine.evaluate(profile)
        # Должно работать, просто меньше результатов
        assert isinstance(recs, list)

    def test_multiple_groups_fire(self) -> None:
        """Типовой профиль должен активировать правила из нескольких групп."""
        engine = PythonRuleEngine()
        profile = make_profile(
            career_goal=CareerGoal.ML,
            semester=4,
            weak_math=True,
            coverage=CoverageLevel.LOW,
        )
        recs = engine.evaluate(profile)
        categories = {r.category for r in recs}
        assert len(categories) >= 3  # минимум CK_COURSE + FOCUS + WARNING

    def test_trace_fired_ids_format(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)
        trace, _ = engine.evaluate_with_trace(profile)
        for rule_id in trace.rules_fired_ids:
            assert rule_id.startswith("R")
            assert rule_id[1:].isdigit()

    def test_high_coverage_triggers_strategy(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(coverage=CoverageLevel.HIGH)
        recs = engine.evaluate(profile)
        r49 = [r for r in recs if r.rule_id == "R49"]
        assert len(r49) == 1
        assert r49[0].priority == RecommendationPriority.MEDIUM

    def test_synergy_fires_when_tp_matches_goal(self) -> None:
        engine = PythonRuleEngine()
        profile = make_profile(
            career_goal=CareerGoal.BACKEND,
            technopark_status=TechparkStatus.BACKEND,
        )
        recs = engine.evaluate(profile)
        r50 = [r for r in recs if r.rule_id == "R50"]
        assert len(r50) == 1
