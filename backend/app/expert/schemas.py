from __future__ import annotations

import enum
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    TechparkStatus,
    WorkloadPref,
)


class CKDevStatus(enum.StrEnum):
    """X6: статус прохождения программ ЦК по разработке."""

    YES = "yes"
    NO = "no"
    PARTIAL = "partial"


class CoverageLevel(enum.StrEnum):
    """X11: покрытие целевого профиля компетенций."""

    LOW = "low"  # <30%
    MEDIUM = "medium"  # 30-70%
    HIGH = "high"  # >70%


class CKCategoryCount(enum.StrEnum):
    """X12: количество программ ЦК одной категории."""

    FEW = "few"  # 0-2
    MANY = "many"  # >=3


class StudentProfile(BaseModel):
    """Входные данные ЭС — формируются из User и связанных сущностей.

    Параметры X1-X12 из спецификации МЭС.
    """

    user_id: uuid.UUID
    semester: int = Field(ge=1, le=8)  # X2: 1-8
    career_goal: CareerGoal  # X1
    technopark_status: TechparkStatus  # X3
    workload_pref: WorkloadPref  # X4
    completed_ck_ml: bool = False  # X5
    ck_dev_status: CKDevStatus = CKDevStatus.NO  # X6
    completed_ck_security: bool = False  # X7
    completed_ck_testing: bool = False  # X8
    weak_math: bool = False  # X9
    weak_programming: bool = False  # X10
    coverage: CoverageLevel = CoverageLevel.LOW  # X11
    ck_count_in_category: CKCategoryCount = CKCategoryCount.FEW  # X12


class CKCourseLink(BaseModel):
    """Минимальная инфа о привязанном курсе ЦК — для UI-обогащения карточки.

    Заполняется только для рекомендаций category=ck_course, у которых
    `Recommendation.title` совпадает с `ck_courses.name`. Для остальных
    категорий (focus/coursework/technopark/warning/strategy) — None.
    """

    name: str
    description: str | None = None
    category: str
    credits: int


class Recommendation(BaseModel):
    """Одна рекомендация экспертной системы."""

    rule_id: str
    category: RecommendationCategory
    title: str
    priority: RecommendationPriority
    reasoning: str
    competency_gap: str | None = None
    # Опциональное обогащение: если category=ck_course и title совпал
    # с записью в ck_courses — приходит детальная инфа курса.
    linked_course: CKCourseLink | None = None


class RecommendationSnapshot(BaseModel):
    """Снимок рекомендаций в момент изменения профиля (для ленты /history)."""

    id: uuid.UUID
    created_at: datetime
    recommendations: list[Recommendation]
    profile_change_summary: str | None = None

    model_config = {"from_attributes": True}
