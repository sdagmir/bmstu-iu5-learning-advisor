"""Сервис экспертной системы — тонкая обёртка над движком."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.expert.engine import EvaluationTrace, PythonRuleEngine, RuleData
from app.expert.rules_data import get_all_rules

if TYPE_CHECKING:
    from app.expert.schemas import Recommendation, StudentProfile


def _build_engine_from_seed() -> PythonRuleEngine:
    """Создание движка из seed-данных (для тестов и работы без БД)."""
    rules = [RuleData(**r) for r in get_all_rules()]
    return PythonRuleEngine(rules=rules)


class ExpertService:
    def __init__(self) -> None:
        # По умолчанию — из seed-данных. В продакшене перезагружается из БД.
        self._engine = _build_engine_from_seed()

    async def reload_from_db(self, db: object) -> None:
        """Перезагрузка production-движка из БД. Только опубликованные правила.

        Вызывается на старте и после publish/unpublish/изменения опубликованного правила.
        """
        self._engine = await PythonRuleEngine.from_db(db)

    def get_recommendations(self, profile: StudentProfile) -> list[Recommendation]:
        return self._engine.evaluate(profile)

    def get_recommendations_debug(
        self, profile: StudentProfile
    ) -> tuple[EvaluationTrace, list[Recommendation]]:
        return self._engine.evaluate_with_trace(profile)

    async def preview(
        self,
        profile: StudentProfile,
        db: object,
        *,
        include_drafts: bool = True,
    ) -> tuple[EvaluationTrace, list[Recommendation]]:
        """Прогон ЭС в одноразовом движке для конструктора.

        По умолчанию загружает published + черновики, чтобы админ увидел эффект
        от своих изменений до публикации. На production-движок не влияет.
        """
        temp_engine = await PythonRuleEngine.from_db(db, include_drafts=include_drafts)
        return temp_engine.evaluate_with_trace(profile)

    @property
    def rule_count(self) -> int:
        return self._engine.rule_count


expert_service = ExpertService()
