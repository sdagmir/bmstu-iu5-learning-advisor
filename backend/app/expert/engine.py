"""Движок экспертной системы — DB-driven.

Правила хранятся в БД как JSON-условия, загружаются при инициализации.
Для тестов без БД: можно передать правила напрямую через конструктор.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from app.expert.evaluator import evaluate_condition

if TYPE_CHECKING:
    from app.expert.schemas import Recommendation, StudentProfile

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class RuleData:
    """Данные одного правила, загруженные из БД или seed."""

    number: int
    group: str
    name: str
    description: str = ""
    condition: dict[str, Any] = field(default_factory=dict)
    recommendation: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    is_active: bool = True


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


# Порядок групп (соответствует документации)
_GROUP_ORDER: dict[str, int] = {
    "ck_programs": 0,
    "basic_universal": 1,
    "technopark": 2,
    "discipline_focus": 3,
    "coursework": 4,
    "warnings": 5,
    "strategy": 6,
}


def _build_recommendation(rule: RuleData, profile_data: dict[str, Any]) -> Recommendation:
    """Построить Recommendation из JSON-шаблона правила."""
    from app.expert.schemas import Recommendation

    rec_data = dict(rule.recommendation)
    rec_data["rule_id"] = f"R{rule.number}"

    # Подстановка шаблонных переменных вида {career_goal_area}
    title = rec_data.get("title", "")
    if "{" in title:
        rec_data["title"] = title.format_map(_TemplateResolver(profile_data, rule))
    reasoning = rec_data.get("reasoning", "")
    if "{" in reasoning:
        rec_data["reasoning"] = reasoning.format_map(_TemplateResolver(profile_data, rule))

    return Recommendation(**rec_data)


class _TemplateResolver(dict):  # type: ignore[type-arg]
    """Резолвер для str.format_map — подставляет значения из профиля и маппингов."""

    def __init__(self, profile: dict[str, Any], rule: RuleData) -> None:
        super().__init__()
        self._profile = profile
        self._rule = rule

    def __missing__(self, key: str) -> str:
        # Прямое значение из профиля
        if key in self._profile:
            return str(self._profile[key])
        # Маппинг из метаданных правила
        mappings = self._rule.recommendation.get("mappings", {})
        if key in mappings:
            mapping = mappings[key]
            lookup_key = str(self._profile.get(mapping["from_param"], ""))
            return mapping["map"].get(lookup_key, mapping.get("default", key))
        return f"{{{key}}}"


class PythonRuleEngine:
    """Детерминированный движок ЭС. DB-driven.

    Реализует протокол ExpertEngine.
    Семантика чистой функции: один вход → один выход, без побочных эффектов.
    """

    def __init__(self, rules: list[RuleData] | None = None) -> None:
        if rules is not None:
            self._rules = sorted(
                [r for r in rules if r.is_active],
                key=lambda r: (_GROUP_ORDER.get(r.group, 99), r.number),
            )
        else:
            self._rules = []
        logger.info("Движок ЭС инициализирован: %d правил", len(self._rules))

    @classmethod
    async def from_db(cls, db: object, *, include_drafts: bool = False) -> PythonRuleEngine:
        """Загрузка правил из БД.

        - include_drafts=False (default) — только опубликованные active-правила.
          Используется для production-движка, обслуживающего студентов.
        - include_drafts=True — published + черновики. Для admin-preview.
        """
        from sqlalchemy import select

        from app.db.models import Rule

        stmt = select(Rule).where(Rule.is_active.is_(True))
        if not include_drafts:
            stmt = stmt.where(Rule.is_published.is_(True))

        result = await db.execute(stmt)  # type: ignore[union-attr]
        db_rules = result.scalars().all()

        rules = [
            RuleData(
                number=r.number,
                group=r.group,
                name=r.name,
                description=r.description,
                condition=r.condition,
                recommendation=r.recommendation,
                priority=r.priority,
                is_active=r.is_active,
            )
            for r in db_rules
        ]
        return cls(rules=rules)

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
        profile_data = profile.model_dump(mode="json")
        trace = EvaluationTrace(profile_snapshot=profile_data)
        recommendations: list[Recommendation] = []

        for rule in self._rules:
            entry = RuleTraceEntry(
                rule_number=rule.number,
                rule_name=rule.name,
                group=rule.group,
            )

            try:
                fired = evaluate_condition(rule.condition, profile_data)
            except Exception as exc:
                logger.exception("Правило R%d вызвало исключение", rule.number)
                entry.skipped_reason = f"Исключение: {type(exc).__name__}: {exc}"
                trace.entries.append(entry)
                continue

            if fired:
                entry.fired = True
                trace.fired_rule_numbers.append(rule.number)
                try:
                    rec = _build_recommendation(rule, profile_data)
                    recommendations.append(rec)
                except Exception as exc:
                    logger.exception("Ошибка построения рекомендации R%d", rule.number)
                    entry.skipped_reason = f"Ошибка рекомендации: {exc}"
                    entry.fired = False
            else:
                entry.skipped_reason = "Условие не выполнено"

            trace.entries.append(entry)

        return trace, recommendations

    @property
    def rule_count(self) -> int:
        return len(self._rules)
