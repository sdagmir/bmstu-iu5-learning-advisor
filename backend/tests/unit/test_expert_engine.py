from __future__ import annotations

import pytest

from app.db.models import CareerGoal, RecommendationPriority, TechparkStatus
from app.expert.engine import PythonRuleEngine, RuleData
from app.expert.rules_data import get_all_rules
from app.expert.schemas import CoverageLevel
from tests.conftest import make_profile


def _make_engine() -> PythonRuleEngine:
    """Создание движка из seed-данных для тестов."""
    rules = [RuleData(**r) for r in get_all_rules()]
    return PythonRuleEngine(rules=rules)


class TestRuleData:
    def test_all_52_rules_loaded(self) -> None:
        rules = get_all_rules()
        assert len(rules) == 52

    def test_no_duplicate_numbers(self) -> None:
        rules = get_all_rules()
        numbers = [r["number"] for r in rules]
        assert len(numbers) == len(set(numbers))

    def test_all_groups_present(self) -> None:
        rules = get_all_rules()
        groups = {r["group"] for r in rules}
        expected = {
            "ck_programs",
            "basic_universal",
            "technopark",
            "discipline_focus",
            "coursework",
            "warnings",
            "strategy",
        }
        assert groups == expected

    def test_all_rules_have_condition(self) -> None:
        for r in get_all_rules():
            assert "condition" in r, f"R{r['number']} без condition"
            assert "all" in r["condition"] or "any" in r["condition"] or "param" in r["condition"]

    def test_all_rules_have_recommendation(self) -> None:
        for r in get_all_rules():
            assert "recommendation" in r, f"R{r['number']} без recommendation"
            rec = r["recommendation"]
            assert "category" in rec
            assert "title" in rec
            assert "priority" in rec


class TestPythonRuleEngine:
    def test_satisfies_protocol(self) -> None:
        engine = _make_engine()
        assert hasattr(engine, "evaluate")
        assert callable(engine.evaluate)

    def test_rule_count(self) -> None:
        engine = _make_engine()
        assert engine.rule_count == 52

    def test_deterministic_output(self) -> None:
        engine = _make_engine()
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)
        r1 = engine.evaluate(profile)
        r2 = engine.evaluate(profile)
        assert [r.rule_id for r in r1] == [r.rule_id for r in r2]

    def test_trace_covers_all_rules(self) -> None:
        engine = _make_engine()
        profile = make_profile()
        trace, _ = engine.evaluate_with_trace(profile)
        assert trace.total_checked == 52

    def test_trace_profile_snapshot(self) -> None:
        engine = _make_engine()
        profile = make_profile(career_goal=CareerGoal.BACKEND, semester=3)
        trace, _ = engine.evaluate_with_trace(profile)
        assert trace.profile_snapshot["career_goal"] == "backend"
        assert trace.profile_snapshot["semester"] == 3

    def test_undecided_student_gets_recommendations(self) -> None:
        engine = _make_engine()
        profile = make_profile(career_goal=CareerGoal.UNDECIDED, semester=2)
        recs = engine.evaluate(profile)
        assert len(recs) > 0

    def test_multiple_groups_fire(self) -> None:
        """Типичный профиль должен активировать правила из нескольких групп."""
        engine = _make_engine()
        profile = make_profile(
            career_goal=CareerGoal.ML, semester=4, weak_math=True, coverage=CoverageLevel.LOW
        )
        recs = engine.evaluate(profile)
        categories = {r.category for r in recs}
        assert len(categories) >= 3

    def test_trace_fired_ids_format(self) -> None:
        engine = _make_engine()
        profile = make_profile(career_goal=CareerGoal.ML, semester=4)
        trace, _ = engine.evaluate_with_trace(profile)
        for rule_id in trace.rules_fired_ids:
            assert rule_id.startswith("R")
            assert rule_id[1:].isdigit()

    def test_high_coverage_triggers_strategy(self) -> None:
        engine = _make_engine()
        profile = make_profile(coverage=CoverageLevel.HIGH)
        recs = engine.evaluate(profile)
        r49 = [r for r in recs if r.rule_id == "R49"]
        assert len(r49) == 1
        assert r49[0].priority == RecommendationPriority.MEDIUM

    def test_synergy_fires_when_tp_matches_goal(self) -> None:
        engine = _make_engine()
        profile = make_profile(
            career_goal=CareerGoal.BACKEND, technopark_status=TechparkStatus.BACKEND
        )
        recs = engine.evaluate(profile)
        r50 = [r for r in recs if r.rule_id == "R50"]
        assert len(r50) == 1

    def test_inactive_rules_excluded(self) -> None:
        """Правила с is_active=False не вычисляются."""
        all_rules = get_all_rules()
        rules = [RuleData(**r, is_active=(r["number"] != 1)) for r in all_rules]
        engine = PythonRuleEngine(rules=rules)
        assert engine.rule_count == 51

        profile = make_profile(career_goal=CareerGoal.ML, semester=4)
        recs = engine.evaluate(profile)
        assert not any(r.rule_id == "R1" for r in recs)


class TestEvaluator:
    """Тесты интерпретатора условий."""

    def test_eq_operator(self) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {"all": [{"param": "career_goal", "op": "eq", "value": "ml"}]}
        assert evaluate_condition(cond, {"career_goal": "ml"}) is True
        assert evaluate_condition(cond, {"career_goal": "backend"}) is False

    def test_gte_operator(self) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {"all": [{"param": "semester", "op": "gte", "value": 4}]}
        assert evaluate_condition(cond, {"semester": 4}) is True
        assert evaluate_condition(cond, {"semester": 3}) is False

    def test_in_operator(self) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {"all": [{"param": "semester", "op": "in", "value": [2, 3, 4]}]}
        assert evaluate_condition(cond, {"semester": 3}) is True
        assert evaluate_condition(cond, {"semester": 5}) is False

    def test_all_requires_all(self) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {
            "all": [
                {"param": "a", "op": "eq", "value": 1},
                {"param": "b", "op": "eq", "value": 2},
            ]
        }
        assert evaluate_condition(cond, {"a": 1, "b": 2}) is True
        assert evaluate_condition(cond, {"a": 1, "b": 3}) is False

    def test_lookup_eq(self) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {
            "all": [
                {
                    "param": "technopark_status",
                    "op": "lookup_eq",
                    "value": None,
                    "key_param": "career_goal",
                    "map": {"backend": "backend", "ml": "ml"},
                },
            ]
        }
        assert (
            evaluate_condition(cond, {"technopark_status": "backend", "career_goal": "backend"})
            is True
        )
        assert (
            evaluate_condition(cond, {"technopark_status": "ml", "career_goal": "backend"})
            is False
        )

    @pytest.mark.parametrize(
        "op,value,actual,expected",
        [
            ("neq", "none", "backend", True),
            ("neq", "none", "none", False),
            ("gt", 5, 6, True),
            ("gt", 5, 5, False),
            ("lt", 5, 4, True),
            ("lte", 5, 5, True),
            ("not_in", [1, 2], 3, True),
            ("not_in", [1, 2], 1, False),
        ],
    )
    def test_operators(self, op: str, value: object, actual: object, expected: bool) -> None:
        from app.expert.evaluator import evaluate_condition

        cond = {"all": [{"param": "x", "op": op, "value": value}]}
        assert evaluate_condition(cond, {"x": actual}) is expected
