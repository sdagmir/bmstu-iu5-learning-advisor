"""Тесты UserService — схемы для пройденных ЦК и оценок по дисциплинам."""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.users.schemas import (
    CompletedCKAdd,
    CompletedCKRead,
    GradeEntry,
    GradeRead,
    GradesBulk,
    ProfileUpdate,
)


class TestSchemas:
    """Тесты схем для пройденных ЦК и оценок."""

    def test_completed_ck_add(self) -> None:
        """CompletedCKAdd принимает ck_course_id."""
        course_id = uuid.uuid4()
        body = CompletedCKAdd(ck_course_id=course_id)
        assert body.ck_course_id == course_id

    def test_grade_entry_valid(self) -> None:
        """GradeEntry принимает оценку 2-5."""
        entry = GradeEntry(discipline_id=uuid.uuid4(), grade=4)
        assert entry.grade == 4

    def test_grade_entry_min(self) -> None:
        """Минимальная оценка — 2."""
        entry = GradeEntry(discipline_id=uuid.uuid4(), grade=2)
        assert entry.grade == 2

    def test_grade_entry_max(self) -> None:
        """Максимальная оценка — 5."""
        entry = GradeEntry(discipline_id=uuid.uuid4(), grade=5)
        assert entry.grade == 5

    def test_grade_entry_invalid_low(self) -> None:
        """Оценка < 2 → ошибка валидации."""
        with pytest.raises(ValidationError):
            GradeEntry(discipline_id=uuid.uuid4(), grade=1)

    def test_grade_entry_invalid_high(self) -> None:
        """Оценка > 5 → ошибка валидации."""
        with pytest.raises(ValidationError):
            GradeEntry(discipline_id=uuid.uuid4(), grade=6)

    def test_grades_bulk_empty(self) -> None:
        """Пустой список оценок — допустимо (сброс)."""
        body = GradesBulk(grades=[])
        assert body.grades == []

    def test_grades_bulk_multiple(self) -> None:
        """Множественные оценки."""
        grades = [
            GradeEntry(discipline_id=uuid.uuid4(), grade=5),
            GradeEntry(discipline_id=uuid.uuid4(), grade=3),
        ]
        body = GradesBulk(grades=grades)
        assert len(body.grades) == 2

    def test_profile_update_semester_range(self) -> None:
        """ProfileUpdate: семестр в диапазоне 1-8."""
        assert ProfileUpdate(semester=1).semester == 1
        assert ProfileUpdate(semester=8).semester == 8

    def test_profile_update_semester_invalid(self) -> None:
        """ProfileUpdate: семестр за пределами → ошибка."""
        with pytest.raises(ValidationError):
            ProfileUpdate(semester=0)
        with pytest.raises(ValidationError):
            ProfileUpdate(semester=9)


class TestCompletedCKRead:
    """Тесты схемы CompletedCKRead."""

    def test_from_data(self) -> None:
        from app.db.models import CKCourseCategory

        read = CompletedCKRead(
            ck_course_id=uuid.uuid4(),
            ck_course_name="Инженер ML",
            ck_course_category=CKCourseCategory.ML,
            completed_at="2026-01-15T12:00:00",
        )
        assert read.ck_course_name == "Инженер ML"
        assert read.ck_course_category == CKCourseCategory.ML


class TestGradeRead:
    """Тесты схемы GradeRead."""

    def test_from_data(self) -> None:
        read = GradeRead(
            discipline_id=uuid.uuid4(),
            discipline_name="Математический анализ",
            grade=4,
        )
        assert read.discipline_name == "Математический анализ"
        assert read.grade == 4
