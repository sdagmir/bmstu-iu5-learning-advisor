from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.users.schemas import (
    CompletedCKAdd,
    CompletedCKRead,
    GradeRead,
    GradesBulk,
    ProfileUpdate,
    UserRead,
)
from app.users.service import user_service
from app.users.workload import WorkloadSummary, compute_workload

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_profile(body: ProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    updated = await user_service.update_profile(user, body, db)
    return UserRead.model_validate(updated)


@router.get("/me/workload", response_model=WorkloadSummary)
async def get_workload(user: CurrentUser, db: DbSession) -> WorkloadSummary:
    """Расчёт учебной нагрузки: е.з. по семестрам + ЦК + Технопарк."""
    return await compute_workload(user, db)


# ── Пройденные ЦК ──────────────────────────────────────────────────────────


@router.get("/me/completed-ck", response_model=list[CompletedCKRead])
async def list_completed_ck(user: CurrentUser, db: DbSession) -> list[CompletedCKRead]:
    """Список пройденных программ ЦК текущего студента."""
    items = await user_service.list_completed_ck(user.id, db)
    return [
        CompletedCKRead(
            ck_course_id=item.ck_course_id,
            ck_course_name=item.ck_course.name,
            ck_course_category=item.ck_course.category,
            completed_at=item.completed_at,
        )
        for item in items
    ]


@router.post("/me/completed-ck", response_model=CompletedCKRead, status_code=201)
async def add_completed_ck(
    body: CompletedCKAdd, user: CurrentUser, db: DbSession
) -> CompletedCKRead:
    """Отметить ЦК как пройденную."""
    item = await user_service.add_completed_ck(user.id, body.ck_course_id, db)
    return CompletedCKRead(
        ck_course_id=item.ck_course_id,
        ck_course_name=item.ck_course.name,
        ck_course_category=item.ck_course.category,
        completed_at=item.completed_at,
    )


@router.delete("/me/completed-ck/{ck_course_id}", status_code=204)
async def remove_completed_ck(
    ck_course_id: uuid.UUID, user: CurrentUser, db: DbSession
) -> None:
    """Убрать ЦК из пройденных."""
    await user_service.remove_completed_ck(user.id, ck_course_id, db)


# ── Оценки по дисциплинам ──────────────────────────────────────────────────


@router.get("/me/grades", response_model=list[GradeRead])
async def list_grades(user: CurrentUser, db: DbSession) -> list[GradeRead]:
    """Оценки текущего студента по дисциплинам."""
    items = await user_service.list_grades(user.id, db)
    return [
        GradeRead(
            discipline_id=item.discipline_id,
            discipline_name=item.discipline.name,
            grade=item.grade,
        )
        for item in items
    ]


@router.put("/me/grades", response_model=list[GradeRead])
async def set_grades(
    body: GradesBulk, user: CurrentUser, db: DbSession
) -> list[GradeRead]:
    """Полная замена оценок по дисциплинам."""
    items = await user_service.set_grades(user.id, body.grades, db)
    return [
        GradeRead(
            discipline_id=item.discipline_id,
            discipline_name=item.discipline.name,
            grade=item.grade,
        )
        for item in items
    ]
