"""Расчёт учебной нагрузки студента в единицах занятости (е.з.).

Константы:
- Программа ЦК = credits из БД (обычно 2 е.з.)
- Технопарк = 6 е.з. за семестр участия
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import func, select

from app.db.models import (
    CKCourse,
    Discipline,
    StudentCompletedCK,
    TechparkStatus,
)

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models import User

TECHNOPARK_CREDITS = 6  # е.з. Технопарка за семестр


class SemesterWorkload(BaseModel):
    """Нагрузка за один семестр."""

    semester: int
    mandatory_credits: int  # обязательные дисциплины
    elective_credits: int   # элективные дисциплины
    total_curriculum: int   # итого по учебному плану


class WorkloadSummary(BaseModel):
    """Сводка нагрузки студента."""

    current_semester: int
    semesters: list[SemesterWorkload]
    completed_ck_credits: int     # е.з. пройденных ЦК суммарно
    technopark_credits: int       # е.з. Технопарка (0 или TECHNOPARK_CREDITS)
    total_extra_credits: int      # ЦК + ТП


async def compute_workload(user: User, db: AsyncSession) -> WorkloadSummary:
    """Рассчитать нагрузку студента по семестрам."""
    semester = user.semester or 1
    technopark_status = (
        TechparkStatus(user.technopark_status)
        if user.technopark_status
        else TechparkStatus.NONE
    )

    # Нагрузка по семестрам из учебного плана
    result = await db.execute(
        select(
            Discipline.semester,
            Discipline.type,
            func.sum(Discipline.credits),
        )
        .group_by(Discipline.semester, Discipline.type)
        .order_by(Discipline.semester)
    )
    rows = result.all()

    # Собираем по семестрам
    sem_data: dict[int, dict[str, int]] = {}
    for sem, disc_type, total in rows:
        if sem not in sem_data:
            sem_data[sem] = {"mandatory": 0, "elective": 0}
        if disc_type == "mandatory":
            sem_data[sem]["mandatory"] += total
        else:
            sem_data[sem]["elective"] += total

    semesters = [
        SemesterWorkload(
            semester=s,
            mandatory_credits=data.get("mandatory", 0),
            elective_credits=data.get("elective", 0),
            total_curriculum=data.get("mandatory", 0) + data.get("elective", 0),
        )
        for s, data in sorted(sem_data.items())
    ]

    # Е.з. пройденных ЦК
    ck_credits = await _sum_completed_ck_credits(user.id, db)

    # Е.з. Технопарка
    tp_credits = TECHNOPARK_CREDITS if technopark_status != TechparkStatus.NONE else 0

    return WorkloadSummary(
        current_semester=semester,
        semesters=semesters,
        completed_ck_credits=ck_credits,
        technopark_credits=tp_credits,
        total_extra_credits=ck_credits + tp_credits,
    )


async def _sum_completed_ck_credits(user_id: uuid.UUID, db: AsyncSession) -> int:
    """Суммарные е.з. пройденных программ ЦК."""
    result = await db.execute(
        select(func.coalesce(func.sum(CKCourse.credits), 0))
        .join(StudentCompletedCK, CKCourse.id == StudentCompletedCK.ck_course_id)
        .where(StudentCompletedCK.user_id == user_id)
    )
    return int(result.scalar_one())
