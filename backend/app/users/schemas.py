from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import (
    CareerGoal,
    CKCourseCategory,
    TechparkStatus,
    UserRole,
    WorkloadPref,
)


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    semester: int | None
    career_goal: CareerGoal | None
    technopark_status: TechparkStatus | None
    workload_pref: WorkloadPref | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    semester: int | None = Field(default=None, ge=1, le=8)
    career_goal: CareerGoal | None = None
    technopark_status: TechparkStatus | None = None
    workload_pref: WorkloadPref | None = None


# ── Пройденные ЦК ──────────────────────────────────────────────────────────


class CompletedCKRead(BaseModel):
    """Пройденная программа ЦК студента."""

    ck_course_id: uuid.UUID
    ck_course_name: str
    ck_course_category: CKCourseCategory
    completed_at: datetime

    model_config = {"from_attributes": True}


class CompletedCKAdd(BaseModel):
    """Добавление пройденной ЦК."""

    ck_course_id: uuid.UUID


# ── Оценки по дисциплинам ───────────────────────────────────────────────────


class GradeRead(BaseModel):
    """Оценка студента по дисциплине."""

    discipline_id: uuid.UUID
    discipline_name: str
    grade: int

    model_config = {"from_attributes": True}


class GradeEntry(BaseModel):
    """Элемент списка оценок."""

    discipline_id: uuid.UUID
    grade: int = Field(ge=2, le=5)


class GradesBulk(BaseModel):
    """Массовая замена оценок по дисциплинам."""

    grades: list[GradeEntry]
