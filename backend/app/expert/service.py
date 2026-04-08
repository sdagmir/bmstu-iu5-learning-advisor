from __future__ import annotations

from typing import TYPE_CHECKING

from app.expert.engine import EvaluationTrace, PythonRuleEngine

if TYPE_CHECKING:
    from app.expert.schemas import Recommendation, StudentProfile


class ExpertService:
    def __init__(self) -> None:
        self._engine = PythonRuleEngine()

    def get_recommendations(self, profile: StudentProfile) -> list[Recommendation]:
        return self._engine.evaluate(profile)

    def get_recommendations_debug(
        self, profile: StudentProfile
    ) -> tuple[EvaluationTrace, list[Recommendation]]:
        return self._engine.evaluate_with_trace(profile)

    @property
    def rule_count(self) -> int:
        return self._engine.rule_count


expert_service = ExpertService()
