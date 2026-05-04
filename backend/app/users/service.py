from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.models import (
    CKCourse,
    Discipline,
    StudentCompletedCK,
    StudentGrade,
    User,
)
from app.exceptions import ConflictError, NotFoundError

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.users.schemas import GradeEntry, ProfileUpdate

# Человекочитаемые подписи X1–X4 для summary в истории рекомендаций
_PROFILE_FIELD_LABELS: dict[str, str] = {
    "career_goal": "Цель",
    "semester": "Семестр",
    "technopark_status": "Технопарк",
    "workload_pref": "Нагрузка",
}


def _fmt(value: Any) -> str:
    """Форматирование значения профиля для summary (enum → его str-значение)."""
    if value is None:
        return "—"
    if hasattr(value, "value"):
        return str(value.value)
    return str(value)


class UserService:
    """Сервис управления профилем и учебными данными студента."""

    async def get_by_id(self, user_id: uuid.UUID, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User", str(user_id))
        return user

    async def update_profile(self, user: User, data: ProfileUpdate, db: AsyncSession) -> User:
        """Обновление полей профиля (X1-X4).

        При фактическом изменении X1–X4 фиксирует snapshot рекомендаций в
        `recommendation_history` (для ленты /history).
        """
        update_data = data.model_dump(exclude_unset=True)

        changes: list[str] = []
        for field, value in update_data.items():
            old = getattr(user, field)
            if old != value:
                label = _PROFILE_FIELD_LABELS.get(field, field)
                changes.append(f"{label}: {_fmt(old)} → {_fmt(value)}")
            setattr(user, field, value)
        await db.flush()

        if changes:
            # Локальный импорт — избегаем кругового импорта expert ↔ users
            from app.expert.service import capture_recommendation_snapshot

            await capture_recommendation_snapshot(user, db, "; ".join(changes))

        return user

    # ── Пройденные ЦК ──────────────────────────────────────────────────────

    async def list_completed_ck(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> list[StudentCompletedCK]:
        """Список пройденных ЦК студента."""
        result = await db.execute(
            select(StudentCompletedCK)
            .options(selectinload(StudentCompletedCK.ck_course))
            .where(StudentCompletedCK.user_id == user_id)
            .order_by(StudentCompletedCK.completed_at.desc())
        )
        return list(result.scalars().all())

    async def add_completed_ck(
        self, user_id: uuid.UUID, ck_course_id: uuid.UUID, db: AsyncSession
    ) -> StudentCompletedCK:
        """Добавить пройденную ЦК."""
        course = await db.execute(select(CKCourse).where(CKCourse.id == ck_course_id))
        if course.scalar_one_or_none() is None:
            raise NotFoundError("CKCourse", str(ck_course_id))

        existing = await db.execute(
            select(StudentCompletedCK).where(
                StudentCompletedCK.user_id == user_id,
                StudentCompletedCK.ck_course_id == ck_course_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("CK course already marked as completed")

        entry = StudentCompletedCK(user_id=user_id, ck_course_id=ck_course_id)
        db.add(entry)
        await db.flush()

        result = await db.execute(
            select(StudentCompletedCK)
            .options(selectinload(StudentCompletedCK.ck_course))
            .where(
                StudentCompletedCK.user_id == user_id,
                StudentCompletedCK.ck_course_id == ck_course_id,
            )
        )
        return result.scalar_one()

    async def remove_completed_ck(
        self, user_id: uuid.UUID, ck_course_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Убрать ЦК из пройденных."""
        result = await db.execute(
            select(StudentCompletedCK).where(
                StudentCompletedCK.user_id == user_id,
                StudentCompletedCK.ck_course_id == ck_course_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("CompletedCK", str(ck_course_id))
        await db.delete(entry)
        await db.flush()

    # ── Оценки по дисциплинам ──────────────────────────────────────────────

    async def list_grades(self, user_id: uuid.UUID, db: AsyncSession) -> list[StudentGrade]:
        """Список оценок студента по дисциплинам."""
        result = await db.execute(
            select(StudentGrade)
            .options(selectinload(StudentGrade.discipline))
            .where(StudentGrade.user_id == user_id)
        )
        return list(result.scalars().all())

    async def set_grades(
        self,
        user_id: uuid.UUID,
        grades: list[GradeEntry],
        db: AsyncSession,
    ) -> list[StudentGrade]:
        """Полная замена оценок по дисциплинам."""
        if grades:
            disc_ids = [g.discipline_id for g in grades]
            result = await db.execute(select(Discipline.id).where(Discipline.id.in_(disc_ids)))
            found_ids = {row[0] for row in result.all()}
            missing = [str(d) for d in disc_ids if d not in found_ids]
            if missing:
                raise NotFoundError("Discipline", ", ".join(missing))

        await db.execute(delete(StudentGrade).where(StudentGrade.user_id == user_id))

        for g in grades:
            db.add(
                StudentGrade(
                    user_id=user_id,
                    discipline_id=g.discipline_id,
                    grade=g.grade,
                )
            )
        await db.flush()

        return await self.list_grades(user_id, db)


user_service = UserService()
