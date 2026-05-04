"""Сервис экспертной системы — тонкая обёртка над движком."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import select, update

from app.db.models import RecommendationHistory, Rule
from app.expert.engine import EvaluationTrace, PythonRuleEngine, RuleData
from app.expert.rules_data import get_all_rules
from app.expert.schemas import RecommendationSnapshot
from app.users.profile_builder import build_student_profile

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models import User
    from app.expert.schemas import Recommendation, StudentProfile

logger = logging.getLogger(__name__)


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


async def capture_recommendation_snapshot(
    user: User, db: AsyncSession, change_summary: str | None
) -> None:
    """Зафиксировать рекомендации текущего профиля в историю.

    Вызывается из user_service после изменения X1–X4. Если новый список
    рекомендаций (rule_id-ы) совпадает с последним snapshot'ом — пропускаем,
    чтобы не плодить дубликаты при no-op обновлениях профиля.
    """
    profile = await build_student_profile(user, db)
    recs = expert_service.get_recommendations(profile)
    new_rule_ids = [r.rule_id for r in recs]

    last = await db.execute(
        select(RecommendationHistory)
        .where(RecommendationHistory.user_id == user.id)
        .order_by(RecommendationHistory.created_at.desc())
        .limit(1)
    )
    prev = last.scalar_one_or_none()
    if prev is not None:
        prev_rule_ids = [r.get("rule_id") for r in prev.recommendations]
        if prev_rule_ids == new_rule_ids:
            return

    entry = RecommendationHistory(
        user_id=user.id,
        recommendations=[r.model_dump(mode="json") for r in recs],
        profile_change_summary=change_summary,
    )
    db.add(entry)
    await db.flush()


async def increment_rule_triggers(fired_numbers: list[int], db: AsyncSession) -> None:
    """Увеличить trigger_count у сработавших правил.

    Вызывается ТОЛЬКО из production-путей (/expert/my-recommendations), где
    рекомендации фактически показываются студенту. Не должна вызываться из
    preview/sandbox/what-if (/expert/evaluate, RulesPage preview).

    Обёрнуто в SAVEPOINT: если UPDATE упадёт (lock timeout, broken connection),
    откатится только nested-транзакция — основной запрос /my-recommendations
    спокойно вернёт рекомендации студенту.
    """
    if not fired_numbers:
        return
    try:
        async with db.begin_nested():
            await db.execute(
                update(Rule)
                .where(Rule.number.in_(fired_numbers))
                .values(trigger_count=Rule.trigger_count + 1)
                .execution_options(synchronize_session=False)
            )
    except BaseException:
        # Метрика — best effort: ошибка не должна валить ответ студенту
        logger.exception("Не удалось обновить trigger_count")


async def list_recommendation_history(
    user_id: uuid.UUID, db: AsyncSession, *, offset: int = 0, limit: int = 50
) -> list[RecommendationSnapshot]:
    """Лента снапшотов рекомендаций пользователя (newest first)."""
    result = await db.execute(
        select(RecommendationHistory)
        .where(RecommendationHistory.user_id == user_id)
        .order_by(RecommendationHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    rows = list(result.scalars().all())
    return [RecommendationSnapshot.model_validate(row) for row in rows]
