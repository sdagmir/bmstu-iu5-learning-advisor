"""Безопасное обновление поля description у уже существующих курсов ЦК.

В отличие от seed_ck_courses — этот скрипт НЕ создаёт курсы и НЕ трогает
name/category/credits/связи (competencies, prerequisites). Меняется только
текст description из ck_courses.json.

Запуск на сервере:
    docker exec rs-ito-app python -m app.admin.refresh_courses

Кеша у курсов нет (CKCourse читается на каждый запрос), поэтому
hot-reload не требуется — новые описания подтянутся сразу.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.database import async_session_factory
from app.db.models import CKCourse

logger = logging.getLogger(__name__)
SEED_DATA_DIR = Path(__file__).parent / "seed_data"


async def refresh_descriptions() -> tuple[int, int, int]:
    """Обновить description у всех уже существующих курсов ЦК.

    Возвращает (обновлено, не изменилось, пропущено-нет-в-БД).
    """
    with (SEED_DATA_DIR / "ck_courses.json").open(encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)

    updated = 0
    unchanged = 0
    missing = 0
    async with async_session_factory() as db:
        for item in data:
            name = item["name"]
            new_desc = item.get("description")

            existing = await db.execute(select(CKCourse).where(CKCourse.name == name))
            course = existing.scalar_one_or_none()
            if course is None:
                logger.info("%s: курса нет в БД — пропускаю (запусти seed)", name)
                missing += 1
                continue

            if course.description == new_desc:
                unchanged += 1
                continue

            course.description = new_desc
            updated += 1
            logger.info("%s: description обновлён", name)

        await db.commit()

    return updated, unchanged, missing


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    upd, unc, mis = asyncio.run(refresh_descriptions())
    print(f"\nОбновлено: {upd}, без изменений: {unc}, нет в БД: {mis}")


if __name__ == "__main__":
    main()
