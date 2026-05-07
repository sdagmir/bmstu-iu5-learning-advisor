"""Безопасное обновление поля recommendation у уже существующих правил.

В отличие от seed_rules — этот скрипт НЕ создаёт правила и НЕ перетирает
condition/group/name/description/is_published/edit-locks. Меняется только
JSON-поле recommendation (текст title/reasoning/priority/competency_gap).

Запуск на сервере:
    docker exec rs-ito-app python -m app.admin.refresh_rules

После обновления вызывает expert_service.reload_from_db, чтобы запущенный
движок ЭС подхватил новые тексты без рестарта uvicorn.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.db.database import async_session_factory
from app.db.models import Rule
from app.expert.rules_data import get_all_rules
from app.expert.service import expert_service

logger = logging.getLogger(__name__)


async def refresh_recommendations() -> tuple[int, int]:
    """Обновить recommendation-поле у всех уже существующих правил.

    Возвращает (обновлено, пропущено).
    """
    updated = 0
    skipped = 0
    async with async_session_factory() as db:
        for rule_data in get_all_rules():
            number = rule_data["number"]
            new_rec = rule_data["recommendation"]

            existing = await db.execute(select(Rule).where(Rule.number == number))
            rule = existing.scalar_one_or_none()
            if rule is None:
                logger.info("R%d: правила нет в БД — пропускаю (запусти seed_rules)", number)
                skipped += 1
                continue

            # Обновляем только recommendation; остальные поля (is_published,
            # condition, edit_lock_*) остаются нетронутыми.
            rule.recommendation = new_rec
            updated += 1
            logger.info("R%d: recommendation обновлено", number)

        await db.commit()

        # Hot-reload работающего движка из БД, чтобы /my-recommendations
        # сразу отдавал новые тексты без рестарта контейнера.
        await expert_service.reload_from_db(db)
        logger.info("Движок ЭС перезагружен из БД")

    return updated, skipped


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    upd, skp = asyncio.run(refresh_recommendations())
    print(f"\nОбновлено правил: {upd}, пропущено: {skp}")


if __name__ == "__main__":
    main()
