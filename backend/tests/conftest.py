from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.models import CareerGoal, TechparkStatus, UserRole, WorkloadPref
from app.expert.schemas import (
    CKCategoryCount,
    CKDevStatus,
    CoverageLevel,
    StudentProfile,
)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Мок AsyncSession для юнит-тестов (реальная БД не нужна)."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.add = MagicMock()
    return db


@pytest.fixture
def mock_user() -> MagicMock:
    """Мок пользователя-студента."""
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "student@test.com"
    user.role = UserRole.STUDENT
    user.is_active = True
    user.semester = 4
    user.career_goal = CareerGoal.ML
    user.technopark_status = TechparkStatus.NONE
    user.workload_pref = WorkloadPref.NORMAL
    user.password_hash = "$2b$12$fakehashfortest"
    return user


@pytest.fixture
def mock_admin() -> MagicMock:
    """Мок пользователя-администратора."""
    admin = MagicMock()
    admin.id = uuid.uuid4()
    admin.email = "admin@test.com"
    admin.role = UserRole.ADMIN
    admin.is_active = True
    return admin


def make_profile(**overrides: object) -> StudentProfile:
    """Создание StudentProfile с разумными значениями по умолчанию. Можно переопределить любое поле."""
    defaults: dict[str, object] = {
        "user_id": uuid.uuid4(),
        "semester": 4,
        "career_goal": CareerGoal.UNDECIDED,
        "technopark_status": TechparkStatus.NONE,
        "workload_pref": WorkloadPref.NORMAL,
        "completed_ck_ml": False,
        "ck_dev_status": CKDevStatus.NO,
        "completed_ck_security": False,
        "completed_ck_testing": False,
        "weak_math": False,
        "weak_programming": False,
        "coverage": CoverageLevel.LOW,
        "ck_count_in_category": CKCategoryCount.FEW,
    }
    defaults.update(overrides)
    return StudentProfile(**defaults)  # type: ignore[arg-type]
