from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.expert.registry import RuleSpec
    from app.expert.schemas import Recommendation, StudentProfile

logger = logging.getLogger(__name__)


@dataclass
class RuleTraceEntry:
    """Одна запись в трассировке вычисления."""

    rule_number: int
    rule_name: str
    group: str
    fired: bool = False
    skipped_reason: str | None = None


@dataclass
class EvaluationTrace:
    """Полный журнал аудита одного вызова evaluate()."""

    profile_snapshot: dict[str, object] = field(default_factory=dict)
    entries: list[RuleTraceEntry] = field(default_factory=list)
    fired_rule_numbers: list[int] = field(default_factory=list)

    @property
    def rules_fired_ids(self) -> list[str]:
        """Список вида ['R1', 'R25', 'R42'] для отладочного интерфейса."""
        return [f"R{n}" for n in self.fired_rule_numbers]

    @property
    def total_checked(self) -> int:
        return len(self.entries)

    @property
    def total_fired(self) -> int:
        return len(self.fired_rule_numbers)


class PythonRuleEngine:
    """Детерминированный движок экспертной системы на правилах.

    Реализует протокол ExpertEngine.
    Семантика чистой функции: один вход → один выход, без побочных эффектов.
    """

    def __init__(self) -> None:
        import app.expert.rules  # noqa: F401 — triggers @rule registrations
        from app.expert.registry import registry

        self._rules: list[RuleSpec] = registry.get_all()
        logger.info("Expert engine initialized with %d rules", len(self._rules))

    def evaluate(self, profile: StudentProfile) -> list[Recommendation]:
        """Вычисление всех правил по профилю. Метод протокола."""
        _, recommendations = self._evaluate_with_trace(profile)
        return recommendations

    def evaluate_with_trace(
        self, profile: StudentProfile
    ) -> tuple[EvaluationTrace, list[Recommendation]]:
        """Вычисление с возвратом трассировки и рекомендаций (для отладки)."""
        return self._evaluate_with_trace(profile)

    def _evaluate_with_trace(
        self, profile: StudentProfile
    ) -> tuple[EvaluationTrace, list[Recommendation]]:
        trace = EvaluationTrace(profile_snapshot=profile.model_dump(mode="json"))
        recommendations: list[Recommendation] = []

        for rule_spec in self._rules:
            entry = RuleTraceEntry(
                rule_number=rule_spec.number,
                rule_name=rule_spec.name,
                group=rule_spec.group,
            )

            try:
                result = rule_spec.func(profile)
            except Exception as exc:
                logger.exception("Rule R%d raised an exception", rule_spec.number)
                entry.skipped_reason = f"Exception: {type(exc).__name__}: {exc}"
                trace.entries.append(entry)
                continue

            if result is not None:
                entry.fired = True
                trace.fired_rule_numbers.append(rule_spec.number)
                recommendations.append(result)
            else:
                entry.skipped_reason = "Condition not met"

            trace.entries.append(entry)

        return trace, recommendations

    @property
    def rule_count(self) -> int:
        return len(self._rules)
