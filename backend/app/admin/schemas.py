from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from app.db.models import (
    CKCourseCategory,
    CompetencyCategory,
    DisciplineType,
    RuleGroup,
)

# ── Компетенции ──────────────────────────────────────────────────────────────


class CompetencyCreate(BaseModel):
    tag: str = Field(max_length=50)
    name: str = Field(max_length=255)
    category: CompetencyCategory


class CompetencyUpdate(BaseModel):
    tag: str | None = Field(default=None, max_length=50)
    name: str | None = Field(default=None, max_length=255)
    category: CompetencyCategory | None = None


class CompetencyRead(BaseModel):
    id: uuid.UUID
    tag: str
    name: str
    category: CompetencyCategory

    model_config = {"from_attributes": True}


# ── Дисциплины ───────────────────────────────────────────────────────────────


class DisciplineCreate(BaseModel):
    name: str = Field(max_length=255)
    semester: int = Field(ge=1, le=8)
    credits: int = Field(ge=1)
    type: DisciplineType
    control_form: str = Field(max_length=50)
    department: str | None = Field(default=None, max_length=50)
    competency_ids: list[uuid.UUID] = []


class DisciplineUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    semester: int | None = Field(default=None, ge=1, le=8)
    credits: int | None = Field(default=None, ge=1)
    type: DisciplineType | None = None
    control_form: str | None = Field(default=None, max_length=50)
    department: str | None = None
    competency_ids: list[uuid.UUID] | None = None


class DisciplineRead(BaseModel):
    id: uuid.UUID
    name: str
    semester: int
    credits: int
    type: DisciplineType
    control_form: str
    department: str | None
    competencies: list[CompetencyRead] = []

    model_config = {"from_attributes": True}


# ── Программы цифровой кафедры ───────────────────────────────────────────────


class CKCourseCreate(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = None
    category: CKCourseCategory
    competency_ids: list[uuid.UUID] = []
    prerequisite_ids: list[uuid.UUID] = []


class CKCourseUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    category: CKCourseCategory | None = None
    competency_ids: list[uuid.UUID] | None = None
    prerequisite_ids: list[uuid.UUID] | None = None


class CKCourseRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    category: CKCourseCategory
    competencies: list[CompetencyRead] = []
    prerequisites: list[CompetencyRead] = []

    model_config = {"from_attributes": True}


# ── Карьерные направления ────────────────────────────────────────────────────


class CareerDirectionCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None
    example_jobs: str | None = None
    competency_ids: list[uuid.UUID] = []


class CareerDirectionUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    example_jobs: str | None = None
    competency_ids: list[uuid.UUID] | None = None


class CareerDirectionRead(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    example_jobs: str | None
    competencies: list[CompetencyRead] = []

    model_config = {"from_attributes": True}


# ── Таблица фокусов ─────────────────────────────────────────────────────────


class FocusAdviceCreate(BaseModel):
    discipline_id: uuid.UUID
    career_direction_id: uuid.UUID
    focus_advice: str
    reasoning: str | None = None


class FocusAdviceUpdate(BaseModel):
    focus_advice: str | None = None
    reasoning: str | None = None


class FocusAdviceRead(BaseModel):
    id: uuid.UUID
    discipline_id: uuid.UUID
    career_direction_id: uuid.UUID
    focus_advice: str
    reasoning: str | None

    model_config = {"from_attributes": True}


# ── Правила ЭС ──────────────────────────────────────────────────────────────


class RuleCreate(BaseModel):
    """Создание нового правила ЭС."""

    number: int = Field(ge=1)
    group: RuleGroup
    name: str = Field(max_length=255)
    description: str = ""
    condition: dict
    recommendation: dict
    priority: int = 0
    is_active: bool = True


class RuleUpdate(BaseModel):
    """Обновление правила ЭС. Все поля опциональны."""

    group: RuleGroup | None = None
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    condition: dict | None = None
    recommendation: dict | None = None
    priority: int | None = None
    is_active: bool | None = None


class RuleRead(BaseModel):
    """Правило ЭС — полное представление."""

    id: uuid.UUID
    number: int
    group: RuleGroup
    name: str
    description: str
    condition: dict
    recommendation: dict
    priority: int
    is_active: bool

    model_config = {"from_attributes": True}
