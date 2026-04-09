"""Скрипт начального наполнения БД данными из документации.

Запуск на сервере: python -m app.admin.seed
Идемпотентный — пропускает уже существующие записи по уникальным полям.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from app.db.database import async_session_factory
from app.db.models import (
    CareerDirection,
    CKCourse,
    CKCourseCategory,
    Competency,
    CompetencyCategory,
)

logger = logging.getLogger(__name__)

# ── 38 тегов компетенций (из документации, таблица 3) ────────────────────────

COMPETENCIES = [
    # Программирование
    ("python", "Программирование на Python", CompetencyCategory.PROGRAMMING),
    ("cpp", "Программирование на C/C++", CompetencyCategory.PROGRAMMING),
    ("javascript", "Программирование на JavaScript", CompetencyCategory.PROGRAMMING),
    ("git", "Системы контроля версий (Git)", CompetencyCategory.PROGRAMMING),
    ("linux", "Администрирование Linux", CompetencyCategory.PROGRAMMING),
    ("algorithms", "Алгоритмы и структуры данных", CompetencyCategory.PROGRAMMING),
    # Математика
    ("linear_algebra", "Линейная алгебра", CompetencyCategory.MATH),
    ("calculus", "Математический анализ", CompetencyCategory.MATH),
    ("discrete_math", "Дискретная математика", CompetencyCategory.MATH),
    ("probability", "Теория вероятностей", CompetencyCategory.MATH),
    ("statistics", "Математическая статистика", CompetencyCategory.MATH),
    # Данные
    ("sql", "Базы данных и SQL", CompetencyCategory.DATA),
    ("db_design", "Проектирование баз данных", CompetencyCategory.DATA),
    ("data_analysis", "Анализ данных", CompetencyCategory.DATA),
    ("data_visualization", "Визуализация данных", CompetencyCategory.DATA),
    # Машинное обучение
    ("ml_basics", "Машинное обучение (базовое)", CompetencyCategory.ML),
    ("deep_learning", "Нейронные сети и глубокое обучение", CompetencyCategory.ML),
    ("nlp", "Обработка естественного языка", CompetencyCategory.ML),
    ("computer_vision", "Компьютерное зрение", CompetencyCategory.ML),
    # Инженерия ПО
    ("oop", "Объектно-ориентированное программирование", CompetencyCategory.ENGINEERING),
    ("design_patterns", "Паттерны проектирования", CompetencyCategory.ENGINEERING),
    ("api_design", "Проектирование REST API", CompetencyCategory.ENGINEERING),
    ("docker", "Контейнеризация (Docker)", CompetencyCategory.ENGINEERING),
    ("ci_cd", "Непрерывная интеграция и доставка", CompetencyCategory.ENGINEERING),
    ("testing", "Тестирование ПО", CompetencyCategory.ENGINEERING),
    ("software_architecture", "Архитектура ПО", CompetencyCategory.ENGINEERING),
    # Сети и безопасность
    ("networking", "Компьютерные сети", CompetencyCategory.NETWORKS),
    ("network_protocols", "Сетевые протоколы", CompetencyCategory.NETWORKS),
    ("cryptography", "Криптография", CompetencyCategory.NETWORKS),
    ("pentesting", "Тестирование на проникновение", CompetencyCategory.NETWORKS),
    ("network_security", "Сетевая безопасность", CompetencyCategory.NETWORKS),
    # Системное ПО
    ("computer_architecture", "Архитектура ЭВМ", CompetencyCategory.SYSTEM),
    ("operating_systems", "Операционные системы", CompetencyCategory.SYSTEM),
    ("parallel_computing", "Параллельное программирование", CompetencyCategory.SYSTEM),
    # Прикладное
    ("mobile_dev", "Мобильная разработка", CompetencyCategory.APPLIED),
    ("frontend", "Фронтенд-разработка", CompetencyCategory.APPLIED),
    ("ux_design", "UX/UI проектирование", CompetencyCategory.APPLIED),
    ("game_dev", "Разработка игр", CompetencyCategory.APPLIED),
]

# ── 10 карьерных направлений (из документации, таблица 7) ─────────────────────

CAREER_DIRECTIONS = [
    (
        "ML / Data Science",
        "Машинное обучение, анализ данных, нейронные сети",
        [
            "python",
            "linear_algebra",
            "probability",
            "statistics",
            "ml_basics",
            "deep_learning",
            "data_analysis",
            "sql",
        ],
    ),
    (
        "Бэкенд-разработка",
        "Серверная разработка, API, базы данных, DevOps",
        [
            "python",
            "oop",
            "design_patterns",
            "sql",
            "db_design",
            "api_design",
            "docker",
            "ci_cd",
            "software_architecture",
            "git",
            "linux",
        ],
    ),
    (
        "Фронтенд-разработка",
        "Клиентская веб-разработка, интерфейсы, SPA",
        ["javascript", "frontend", "ux_design", "git", "api_design", "testing"],
    ),
    (
        "Кибербезопасность",
        "Информационная безопасность, пентест, криптография",
        [
            "networking",
            "network_protocols",
            "cryptography",
            "pentesting",
            "network_security",
            "linux",
            "operating_systems",
        ],
    ),
    (
        "Системное программирование",
        "Низкоуровневая разработка, ОС, встраиваемые системы",
        [
            "cpp",
            "computer_architecture",
            "operating_systems",
            "parallel_computing",
            "linux",
            "algorithms",
        ],
    ),
    (
        "DevOps / Инфраструктура",
        "Автоматизация, CI/CD, контейнеризация, мониторинг",
        ["linux", "docker", "ci_cd", "networking", "python", "git", "software_architecture"],
    ),
    (
        "Мобильная разработка",
        "Разработка приложений для мобильных платформ",
        ["mobile_dev", "oop", "design_patterns", "api_design", "ux_design", "git", "testing"],
    ),
    (
        "Геймдев",
        "Разработка компьютерных игр, игровые движки",
        ["cpp", "oop", "algorithms", "linear_algebra", "design_patterns"],
    ),
    (
        "QA / Тестирование",
        "Тестирование ПО, автоматизация тестов",
        ["testing", "python", "sql", "api_design", "git", "linux", "ci_cd"],
    ),
    (
        "Аналитика данных / BI",
        "Анализ данных, визуализация, статистика",
        ["sql", "python", "data_analysis", "data_visualization", "statistics", "probability"],
    ),
]

# ── 20 программ цифровой кафедры (из документации, таблица 10) ────────────────

CK_COURSES_DATA = [
    (
        "Инженер машинного обучения",
        CKCourseCategory.ML,
        ["ml_basics", "python", "data_analysis"],
        ["probability", "python", "linear_algebra"],
    ),
    ("Промпт-инженер", CKCourseCategory.ML, ["ml_basics", "nlp"], ["ml_basics", "linear_algebra"]),
    (
        "Инженер автоматизации разработки и эксплуатации",
        CKCourseCategory.DEVELOPMENT,
        ["docker", "ci_cd", "linux"],
        ["python"],
    ),
    (
        "Обеспечение информационной безопасности",
        CKCourseCategory.SECURITY,
        ["cryptography", "network_security"],
        [],
    ),
    (
        "Тестирование на проникновение",
        CKCourseCategory.SECURITY,
        ["pentesting", "network_security"],
        ["networking", "linux"],
    ),
    (
        "Инженер по безопасности приложений",
        CKCourseCategory.SECURITY,
        ["network_security", "testing"],
        ["python", "git", "linux"],
    ),
    (
        "Разработчик пользовательских интерфейсов",
        CKCourseCategory.DEVELOPMENT,
        ["frontend", "javascript"],
        ["git", "linux"],
    ),
    (
        "Дизайнер пользовательских интерфейсов",
        CKCourseCategory.DEVELOPMENT,
        ["ux_design", "frontend"],
        [],
    ),
    ("Разработка компьютерных игр", CKCourseCategory.DEVELOPMENT, ["cpp", "algorithms"], ["oop"]),
    ("Разработка на C и C++", CKCourseCategory.DEVELOPMENT, ["cpp", "algorithms"], []),
    (
        "Инженер-разработчик встраиваемых систем",
        CKCourseCategory.DEVELOPMENT,
        ["cpp", "computer_architecture"],
        [],
    ),
    (
        "Архитектор платёжных сервисов",
        CKCourseCategory.DEVELOPMENT,
        ["software_architecture", "api_design"],
        ["python", "sql"],
    ),
    (
        "Системный аналитик",
        CKCourseCategory.MANAGEMENT,
        ["db_design", "software_architecture"],
        ["algorithms", "discrete_math"],
    ),
    (
        "Инженер по тестированию производительности",
        CKCourseCategory.TESTING,
        ["testing", "python"],
        ["oop", "sql", "networking"],
    ),
    ("Цифровые навыки", CKCourseCategory.OTHER, ["python", "git", "linux"], []),
    (
        "Специалист по интернет-маркетингу",
        CKCourseCategory.MANAGEMENT,
        ["data_analysis", "data_visualization"],
        [],
    ),
    (
        "Руководитель продукта",
        CKCourseCategory.MANAGEMENT,
        ["software_architecture", "ux_design"],
        [],
    ),
    ("Программист 1С", CKCourseCategory.DEVELOPMENT, ["sql", "db_design"], ["sql"]),
    ("Аналитик 1С", CKCourseCategory.MANAGEMENT, ["sql", "data_analysis"], ["sql"]),
    ("Low-code разработка", CKCourseCategory.DEVELOPMENT, ["api_design", "db_design"], []),
]


async def _get_or_create_competency(
    db: AsyncSession, tag: str, name: str, category: CompetencyCategory
) -> Competency:
    """Получить существующую или создать новую компетенцию."""
    result = await db.execute(select(Competency).where(Competency.tag == tag))
    comp = result.scalar_one_or_none()
    if comp is None:
        comp = Competency(tag=tag, name=name, category=category)
        db.add(comp)
        await db.flush()
        logger.info("  + компетенция: %s", tag)
    return comp


async def seed_competencies(db: AsyncSession) -> dict[str, Competency]:
    """Сидирование 38 компетенций. Возвращает словарь tag → Competency."""
    logger.info("Сидирование компетенций...")
    tag_map: dict[str, Competency] = {}
    for tag, name, category in COMPETENCIES:
        comp = await _get_or_create_competency(db, tag, name, category)
        tag_map[tag] = comp
    logger.info("Компетенций в БД: %d", len(tag_map))
    return tag_map


async def seed_career_directions(db: AsyncSession, tag_map: dict[str, Competency]) -> None:
    """Сидирование 10 карьерных направлений с целевыми профилями."""
    logger.info("Сидирование карьерных направлений...")
    for name, description, comp_tags in CAREER_DIRECTIONS:
        result = await db.execute(select(CareerDirection).where(CareerDirection.name == name))
        if result.scalar_one_or_none() is not None:
            continue
        direction = CareerDirection(name=name, description=description)
        direction.competencies = [tag_map[t] for t in comp_tags if t in tag_map]
        db.add(direction)
        logger.info("  + направление: %s", name)
    await db.flush()


async def seed_ck_courses(db: AsyncSession, tag_map: dict[str, Competency]) -> None:
    """Сидирование 20 программ ЦК с компетенциями и пререквизитами."""
    logger.info("Сидирование программ ЦК...")
    for name, category, comp_tags, prereq_tags in CK_COURSES_DATA:
        result = await db.execute(select(CKCourse).where(CKCourse.name == name))
        if result.scalar_one_or_none() is not None:
            continue
        course = CKCourse(name=name, category=category, credits=2)
        course.competencies = [tag_map[t] for t in comp_tags if t in tag_map]
        course.prerequisites = [tag_map[t] for t in prereq_tags if t in tag_map]
        db.add(course)
        logger.info("  + курс ЦК: %s", name)
    await db.flush()


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


async def run_seed() -> None:
    """Запуск полного сидирования."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    logger.info("=== Начало сидирования БД ===")

    async with async_session_factory() as db:
        try:
            tag_map = await seed_competencies(db)
            await seed_career_directions(db, tag_map)
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
