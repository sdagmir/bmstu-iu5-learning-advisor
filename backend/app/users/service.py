from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.db.models import (
    CareerGoal,
    CKCourse,
    Discipline,
    StudentCompletedCK,
    StudentGrade,
    TechparkStatus,
    User,
    WorkloadPref,
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

# Русские лейблы значений enum'ов профиля — иначе в истории
# светится «backend → cybersecurity» латиницей.
_CAREER_GOAL_RU: dict[CareerGoal, str] = {
    CareerGoal.ML: "ML / Data Science",
    CareerGoal.BACKEND: "Бэкенд-разработка",
    CareerGoal.FRONTEND: "Фронтенд-разработка",
    CareerGoal.CYBERSECURITY: "Кибербезопасность",
    CareerGoal.SYSTEM: "Системное программирование",
    CareerGoal.DEVOPS: "DevOps / Инфраструктура",
    CareerGoal.MOBILE: "Мобильная разработка",
    CareerGoal.GAMEDEV: "Геймдев",
    CareerGoal.QA: "QA / Тестирование",
    CareerGoal.ANALYTICS: "Аналитика данных",
    CareerGoal.UNDECIDED: "Не определена",
}
_TECHPARK_RU: dict[TechparkStatus, str] = {
    TechparkStatus.NONE: "Не участвую",
    TechparkStatus.BACKEND: "Бэкенд",
    TechparkStatus.FRONTEND: "Фронтенд",
    TechparkStatus.ML: "Машинное обучение",
    TechparkStatus.MOBILE: "Мобильная разработка",
}
_WORKLOAD_RU: dict[WorkloadPref, str] = {
    WorkloadPref.LIGHT: "Лёгкая",
    WorkloadPref.NORMAL: "Обычная",
    WorkloadPref.INTENSIVE: "Интенсивная",
}


def _fmt(field: str, value: Any) -> str:
    """Форматирование значения профиля для summary — с русскими лейблами enum'ов.

    Значение может прийти как сам enum (из user-orm) или как строка
    (из Pydantic model_dump) — оба варианта обрабатываем единообразно
    через конструктор enum'а.
    """
    if value is None:
        return "—"
    try:
        if field == "career_goal":
            return _CAREER_GOAL_RU[CareerGoal(value)]
        if field == "technopark_status":
            return _TECHPARK_RU[TechparkStatus(value)]
        if field == "workload_pref":
            return _WORKLOAD_RU[WorkloadPref(value)]
    except (ValueError, KeyError):
        pass
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
        `recommendation_history` (для ленты /history). Snapshot снимается
        ДО применения изменений — чтобы зафиксировать состояние «как было»;
        текущее «как стало» всегда доступно на главной.
        """
        update_data = data.model_dump(exclude_unset=True)

        # 1. Сначала считаем что изменится — без применения, чтобы user ещё
        #    держал старые значения для снимка.
        changes: list[str] = []
        for field, value in update_data.items():
            old = getattr(user, field)
            if old != value:
                label = _PROFILE_FIELD_LABELS.get(field, field)
                changes.append(f"{label}: {_fmt(field, old)} → {_fmt(field, value)}")

        # 2. Если есть фактические изменения — снимаем snapshot до setattr.
        #    Так build_student_profile(user, db) соберёт старый профиль,
        #    а capture_recommendation_snapshot запишет «вот что было».
        #    Best-effort: при ошибке снимка PATCH профиля не должен падать.
        if changes:
            import logging

            from app.expert.service import capture_recommendation_snapshot

            try:
                await capture_recommendation_snapshot(user, db, "; ".join(changes))
            except Exception:
                logging.getLogger(__name__).exception(
                    "Не удалось записать snapshot истории — PATCH профиля продолжается"
                )

        # 3. Теперь применяем изменения и сохраняем.
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.flush()

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
