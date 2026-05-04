"""Расчёт покрытия компетенций для радара /coverage.

«Имею» — компетенции из пройденных ЦК + дисциплин с оценкой ≥ 4.
«Нужно» — целевые компетенции карьерного направления студента.

Возвращает плоский список компетенций (объединение have ∪ needed) с
флагами `has`/`needed` и общий процент покрытия.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import (
    CareerDirection,
    CareerGoal,
    CKCourse,
    Competency,
    CompetencyCategory,
    Discipline,
    StudentCompletedCK,
    StudentGrade,
)
from app.users.profile_builder import _GOAL_TO_DIRECTION_NAME

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models import User

# Минимальная оценка по дисциплине, после которой компетенция считается освоенной
GRADE_THRESHOLD = 4


class CompetencyCoverageItem(BaseModel):
    """Одна компетенция в радаре покрытия."""

    competency_id: str
    name: str
    category: CompetencyCategory
    has: bool
    needed: bool


class CoverageResponse(BaseModel):
    """Радар покрытия компетенций для текущего студента."""

    items: list[CompetencyCoverageItem]
    coverage_percent: float


async def compute_coverage(user: User, db: AsyncSession) -> CoverageResponse:
    """Собрать список компетенций с флагами has/needed и процент покрытия."""
    needed_ids = await _load_needed_ids(user, db)
    has_ids = await _load_has_ids(user.id, db)

    relevant_ids = needed_ids | has_ids
    if not relevant_ids:
        return CoverageResponse(items=[], coverage_percent=0.0)

    result = await db.execute(select(Competency).where(Competency.id.in_(relevant_ids)))
    competencies = list(result.scalars().all())
    competencies.sort(key=lambda c: (c.category.value, c.name))

    items = [
        CompetencyCoverageItem(
            competency_id=str(c.id),
            name=c.name,
            category=c.category,
            has=c.id in has_ids,
            needed=c.id in needed_ids,
        )
        for c in competencies
    ]

    if needed_ids:
        coverage_percent = round(100.0 * len(has_ids & needed_ids) / len(needed_ids), 1)
    else:
        coverage_percent = 0.0

    return CoverageResponse(items=items, coverage_percent=coverage_percent)


async def _load_needed_ids(user: User, db: AsyncSession) -> set[uuid.UUID]:
    """Целевые компетенции карьерного направления студента."""
    if not user.career_goal:
        return set()
    goal = CareerGoal(user.career_goal)
    if goal == CareerGoal.UNDECIDED:
        return set()

    direction_name = _GOAL_TO_DIRECTION_NAME.get(goal)
    if not direction_name:
        return set()

    result = await db.execute(
        select(CareerDirection)
        .options(selectinload(CareerDirection.competencies))
        .where(CareerDirection.name == direction_name)
    )
    direction = result.scalar_one_or_none()
    if not direction:
        return set()
    return {c.id for c in direction.competencies}


async def _load_has_ids(user_id: uuid.UUID, db: AsyncSession) -> set[uuid.UUID]:
    """Освоенные компетенции: пройденные ЦК + дисциплины с оценкой ≥ 4."""
    has_ids: set[uuid.UUID] = set()

    # Из пройденных ЦК
    ck_result = await db.execute(
        select(CKCourse)
        .options(selectinload(CKCourse.competencies))
        .join(StudentCompletedCK, CKCourse.id == StudentCompletedCK.ck_course_id)
        .where(StudentCompletedCK.user_id == user_id)
    )
    courses: list[CKCourse] = list(ck_result.scalars().unique().all())
    for course in courses:
        for comp in course.competencies:
            has_ids.add(comp.id)

    # Из дисциплин с хорошей оценкой
    grade_result = await db.execute(
        select(StudentGrade)
        .options(selectinload(StudentGrade.discipline).selectinload(Discipline.competencies))
        .where(
            StudentGrade.user_id == user_id,
            StudentGrade.grade >= GRADE_THRESHOLD,
        )
    )
    grades: list[StudentGrade] = list(grade_result.scalars().all())
    for sg in grades:
        for comp in sg.discipline.competencies:
            has_ids.add(comp.id)

    return has_ids
