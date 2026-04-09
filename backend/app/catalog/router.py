"""Публичный каталог — read-only доступ к дисциплинам и ЦК для студентов."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.catalog.schemas import CKCourseCatalog, DisciplineCatalog
from app.db.models import CKCourse, Discipline
from app.dependencies import CurrentUser, DbSession

router = APIRouter()


@router.get("/disciplines", response_model=list[DisciplineCatalog])
async def list_disciplines(
    user: CurrentUser,
    db: DbSession,
    semester_max: int | None = Query(default=None, ge=1, le=8, description="Макс. семестр"),
) -> list[DisciplineCatalog]:
    """Каталог дисциплин. Фильтр semester_max — для показа предметов до указанного семестра."""
    query = (
        select(Discipline)
        .options(selectinload(Discipline.competencies))
        .order_by(Discipline.semester, Discipline.name)
    )
    if semester_max is not None:
        query = query.where(Discipline.semester <= semester_max)
    result = await db.execute(query)
    items = list(result.scalars().unique().all())
    return [DisciplineCatalog.model_validate(d) for d in items]


@router.get("/ck-courses", response_model=list[CKCourseCatalog])
async def list_ck_courses(
    user: CurrentUser,
    db: DbSession,
) -> list[CKCourseCatalog]:
    """Каталог программ цифровой кафедры."""
    result = await db.execute(
        select(CKCourse)
        .options(selectinload(CKCourse.competencies), selectinload(CKCourse.prerequisites))
        .order_by(CKCourse.category, CKCourse.name)
    )
    items = list(result.scalars().unique().all())
    return [CKCourseCatalog.model_validate(c) for c in items]
