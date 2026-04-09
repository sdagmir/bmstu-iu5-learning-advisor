"""Скрипт начального наполнения БД данными из JSON-файлов.

Запуск на сервере: python -m app.admin.seed
Идемпотентный — пропускает уже существующие записи по уникальным полям.
Данные хранятся в seed_data/*.json для наглядности и удобства редактирования.
После сидирования всё управляется через Admin API.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.db.database import async_session_factory
from app.db.models import (
    CareerDirection,
    CKCourse,
    CKCourseCategory,
    Competency,
    CompetencyCategory,
    Discipline,
    DisciplineType,
)

logger = logging.getLogger(__name__)
SEED_DATA_DIR = Path(__file__).parent / "seed_data"


def _load_json(filename: str) -> list[dict]:
    """Загрузка данных из JSON-файла."""
    with (SEED_DATA_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


# ── Компетенции ────────────────────────────────────────────────────────────


async def seed_competencies(db: AsyncSession) -> dict[str, Competency]:
    """Сидирование компетенций из competencies.json. Возвращает tag → Competency."""
    logger.info("Сидирование компетенций...")
    data = _load_json("competencies.json")
    tag_map: dict[str, Competency] = {}

    for item in data:
        tag = item["tag"]
        result = await db.execute(select(Competency).where(Competency.tag == tag))
        comp = result.scalar_one_or_none()
        if comp is None:
            comp = Competency(
                tag=tag,
                name=item["name"],
                category=CompetencyCategory(item["category"]),
            )
            db.add(comp)
            await db.flush()
            logger.info("  + компетенция: %s", tag)
        tag_map[tag] = comp

    logger.info("Компетенций в БД: %d", len(tag_map))
    return tag_map


# ── Карьерные направления ──────────────────────────────────────────────────


async def seed_career_directions(db: AsyncSession, tag_map: dict[str, Competency]) -> None:
    """Сидирование карьерных направлений из career_directions.json."""
    logger.info("Сидирование карьерных направлений...")
    data = _load_json("career_directions.json")

    for item in data:
        name = item["name"]
        result = await db.execute(select(CareerDirection).where(CareerDirection.name == name))
        if result.scalar_one_or_none() is not None:
            continue
        direction = CareerDirection(
            name=name,
            description=item.get("description"),
            example_jobs=item.get("example_jobs"),
        )
        direction.competencies = [
            tag_map[t] for t in item.get("competency_tags", []) if t in tag_map
        ]
        db.add(direction)
        logger.info("  + направление: %s", name)
    await db.flush()


# ── Дисциплины ─────────────────────────────────────────────────────────────

_DISCIPLINE_TYPE_MAP = {
    "mandatory": DisciplineType.MANDATORY,
    "elective": DisciplineType.ELECTIVE,
    "choice": DisciplineType.CHOICE,
}


async def seed_disciplines(db: AsyncSession, tag_map: dict[str, Competency]) -> None:
    """Сидирование дисциплин учебного плана из disciplines.json."""
    logger.info("Сидирование дисциплин...")
    data = _load_json("disciplines.json")

    for item in data:
        name = item["name"]
        result = await db.execute(select(Discipline).where(Discipline.name == name))
        if result.scalar_one_or_none() is not None:
            continue
        disc = Discipline(
            name=name,
            semester=item["semester"],
            credits=item["credits"],
            type=_DISCIPLINE_TYPE_MAP[item["type"]],
            control_form=item["control_form"],
            department=item.get("department"),
        )
        disc.competencies = [tag_map[t] for t in item.get("tags", []) if t in tag_map]
        db.add(disc)
        logger.info("  + дисциплина [%d сем.]: %s", item["semester"], name)
    await db.flush()
    logger.info("Дисциплин загружено: %d", len(data))


# ── Программы ЦК ──────────────────────────────────────────────────────────


async def seed_ck_courses(db: AsyncSession, tag_map: dict[str, Competency]) -> None:
    """Сидирование программ ЦК из ck_courses.json."""
    logger.info("Сидирование программ ЦК...")
    data = _load_json("ck_courses.json")

    for item in data:
        name = item["name"]
        result = await db.execute(select(CKCourse).where(CKCourse.name == name))
        if result.scalar_one_or_none() is not None:
            continue
        course = CKCourse(
            name=name,
            description=item.get("description"),
            category=CKCourseCategory(item["category"]),
            credits=item.get("credits", 2),
        )
        course.competencies = [
            tag_map[t] for t in item.get("competency_tags", []) if t in tag_map
        ]
        course.prerequisites = [
            tag_map[t] for t in item.get("prerequisite_tags", []) if t in tag_map
        ]
        db.add(course)
        logger.info("  + курс ЦК: %s", name)
    await db.flush()


# ── Правила ЭС ────────────────────────────────────────────────────────────


async def seed_rules(db: AsyncSession) -> None:
    """Сидирование 52 правил ЭС из rules_data."""
    from app.db.models import Rule
    from app.expert.rules_data import get_all_rules

    logger.info("Сидирование правил ЭС...")
    for rule_data in get_all_rules():
        result = await db.execute(select(Rule).where(Rule.number == rule_data["number"]))
        if result.scalar_one_or_none() is not None:
            continue
        rule = Rule(
            number=rule_data["number"],
            group=rule_data["group"],
            name=rule_data["name"],
            description=rule_data.get("description", ""),
            condition=rule_data["condition"],
            recommendation=rule_data["recommendation"],
            priority=rule_data.get("priority", 0),
        )
        db.add(rule)
        logger.info("  + правило R%d: %s", rule_data["number"], rule_data["name"])
    await db.flush()


# ── Запуск ─────────────────────────────────────────────────────────────────


async def run_seed() -> None:
    """Запуск полного сидирования."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.info("=== Начало сидирования БД ===")

    async with async_session_factory() as db:
        try:
            tag_map = await seed_competencies(db)
            await seed_career_directions(db, tag_map)
            await seed_disciplines(db, tag_map)
            await seed_ck_courses(db, tag_map)
            await seed_rules(db)
            await db.commit()
            logger.info("=== Сидирование завершено ===")
        except Exception:
            await db.rollback()
            logger.exception("Ошибка при сидировании")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
