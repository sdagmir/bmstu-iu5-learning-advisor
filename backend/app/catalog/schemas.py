from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.db.models import CKCourseCategory, CompetencyCategory, DisciplineType


class CompetencyShort(BaseModel):
    """Компетенция — краткое представление для каталога."""

    id: uuid.UUID
    tag: str
    name: str
    category: CompetencyCategory

    model_config = {"from_attributes": True}


class DisciplineCatalog(BaseModel):
    """Дисциплина — представление для каталога."""

    id: uuid.UUID
    name: str
    semester: int
    credits: int
    type: DisciplineType
    control_form: str
    department: str | None
    competencies: list[CompetencyShort] = []

    model_config = {"from_attributes": True}


class CKCourseCatalog(BaseModel):
    """Программа ЦК — представление для каталога."""

    id: uuid.UUID
    name: str
    description: str | None
    category: CKCourseCategory
    credits: int
    competencies: list[CompetencyShort] = []
    prerequisites: list[CompetencyShort] = []

    model_config = {"from_attributes": True}
