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

from app.config import settings
from app.db.database import async_session_factory
from app.db.models import (
    CareerDirection,
    CareerGoal,
    CKCourse,
    CKCourseCategory,
    Competency,
    CompetencyCategory,
    Discipline,
    DisciplineType,
    StudentCompletedCK,
    StudentGrade,
    TechparkStatus,
    User,
    WorkloadPref,
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
        course.competencies = [tag_map[t] for t in item.get("competency_tags", []) if t in tag_map]
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
            # Seed-правила сразу опубликованы — это "shipped" набор для всех студентов
            is_published=True,
        )
        db.add(rule)
        logger.info("  + правило R%d: %s", rule_data["number"], rule_data["name"])
    await db.flush()


# ── Демо-аккаунт ───────────────────────────────────────────────────────────


async def seed_demo_account(db: AsyncSession) -> None:
    """Создать демо-аккаунт для кнопки «Демо для комиссии».

    Профиль: 5-й семестр, цель ML, без ТП, обычная нагрузка, 3 пройденных ЦК
    (ML + Development), все оценки = 4 (без слабых баз). Создаётся только если
    `settings.demo_account_enabled` (на проде выключено).

    Пароль обязателен (`DEMO_ACCOUNT_PASSWORD` в окружении) — не имеет
    default'а в config.py, чтобы случайно не утёк через git.
    """
    if not settings.demo_account_enabled:
        return

    if not settings.demo_account_password:
        msg = (
            "DEMO_ACCOUNT_ENABLED=true, но DEMO_ACCOUNT_PASSWORD пустой. "
            "Задай пароль в окружении сервера (минимум 8 символов)."
        )
        raise ValueError(msg)

    from app.auth.service import auth_service

    email = settings.demo_account_email
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none() is not None:
        logger.info("Демо-аккаунт %s уже существует", email)
        return

    user, _, _ = await auth_service.register(email, settings.demo_account_password, db)
    user.semester = 5
    user.career_goal = CareerGoal.ML
    user.technopark_status = TechparkStatus.NONE
    user.workload_pref = WorkloadPref.NORMAL

    # 3 пройденных ЦК: 2 из ML + 1 из Development (для X5=true, X6=partial)
    ml_courses = await db.execute(
        select(CKCourse).where(CKCourse.category == CKCourseCategory.ML).limit(2)
    )
    dev_courses = await db.execute(
        select(CKCourse).where(CKCourse.category == CKCourseCategory.DEVELOPMENT).limit(1)
    )
    for course in [*ml_courses.scalars().all(), *dev_courses.scalars().all()]:
        db.add(StudentCompletedCK(user_id=user.id, ck_course_id=course.id))

    # Оценки = 4 по всем дисциплинам 1-4 семестра (среднее = 4.0, не слабые базы)
    disciplines = await db.execute(select(Discipline).where(Discipline.semester <= 4))
    for disc in disciplines.scalars().all():
        db.add(StudentGrade(user_id=user.id, discipline_id=disc.id, grade=4))

    await db.flush()
    # Пароль не логируем — даже в demo-режиме лучше не оставлять его в логах сервера
    logger.info("  + демо-аккаунт создан: %s", email)


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
            await seed_demo_account(db)
            await db.commit()
            logger.info("=== Сидирование завершено ===")
        except Exception:
            await db.rollback()
            logger.exception("Ошибка при сидировании")
            raise


if __name__ == "__main__":
    asyncio.run(run_seed())
