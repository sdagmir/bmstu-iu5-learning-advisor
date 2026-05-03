from __future__ import annotations

import uuid  # noqa: TC003 — используется в сигнатурах при рантайме
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import (
    CareerDirection,
    CKCourse,
    Competency,
    Discipline,
    FocusAdvice,
    Rule,
    User,
)
from app.exceptions import NotFoundError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.admin.schemas import (
        CareerDirectionCreate,
        CareerDirectionUpdate,
        CKCourseCreate,
        CKCourseUpdate,
        CompetencyCreate,
        CompetencyUpdate,
        DisciplineCreate,
        DisciplineUpdate,
        FocusAdviceCreate,
        FocusAdviceUpdate,
        RuleCreate,
        RuleUpdate,
        UserAdminUpdate,
    )


# ── Вспомогательные функции ──────────────────────────────────────────────────


async def _load_competencies(db: AsyncSession, ids: list[uuid.UUID]) -> list[Competency]:
    """Загрузка компетенций по списку ID с проверкой существования."""
    if not ids:
        return []
    result = await db.execute(select(Competency).where(Competency.id.in_(ids)))
    found = list(result.scalars().all())
    if len(found) != len(ids):
        found_ids = {c.id for c in found}
        missing = [str(i) for i in ids if i not in found_ids]
        raise NotFoundError("Competency", ", ".join(missing))
    return found


# ── Компетенции ──────────────────────────────────────────────────────────────


class CompetencyService:
    async def list(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 50
    ) -> list[Competency]:
        result = await db.execute(
            select(Competency)
            .order_by(Competency.category, Competency.tag)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, competency_id: uuid.UUID, db: AsyncSession) -> Competency:
        result = await db.execute(select(Competency).where(Competency.id == competency_id))
        comp = result.scalar_one_or_none()
        if comp is None:
            raise NotFoundError("Competency", str(competency_id))
        return comp

    async def create(self, data: CompetencyCreate, db: AsyncSession) -> Competency:
        comp = Competency(tag=data.tag, name=data.name, category=data.category)
        db.add(comp)
        await db.flush()
        return comp

    async def update(
        self, competency_id: uuid.UUID, data: CompetencyUpdate, db: AsyncSession
    ) -> Competency:
        comp = await self.get(competency_id, db)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(comp, field, value)
        await db.flush()
        return comp

    async def delete(self, competency_id: uuid.UUID, db: AsyncSession) -> None:
        comp = await self.get(competency_id, db)
        await db.delete(comp)
        await db.flush()


# ── Дисциплины ───────────────────────────────────────────────────────────────


class DisciplineService:
    async def list(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 50
    ) -> list[Discipline]:
        result = await db.execute(
            select(Discipline)
            .options(selectinload(Discipline.competencies))
            .order_by(Discipline.semester, Discipline.name)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get(self, discipline_id: uuid.UUID, db: AsyncSession) -> Discipline:
        result = await db.execute(
            select(Discipline)
            .options(selectinload(Discipline.competencies))
            .where(Discipline.id == discipline_id)
        )
        disc = result.scalar_one_or_none()
        if disc is None:
            raise NotFoundError("Discipline", str(discipline_id))
        return disc

    async def create(self, data: DisciplineCreate, db: AsyncSession) -> Discipline:
        comps = await _load_competencies(db, data.competency_ids)
        disc = Discipline(
            name=data.name,
            semester=data.semester,
            credits=data.credits,
            type=data.type,
            control_form=data.control_form,
            department=data.department,
        )
        disc.competencies = comps
        db.add(disc)
        await db.flush()
        return disc

    async def update(
        self, discipline_id: uuid.UUID, data: DisciplineUpdate, db: AsyncSession
    ) -> Discipline:
        disc = await self.get(discipline_id, db)
        update_data = data.model_dump(exclude_unset=True)
        if "competency_ids" in update_data:
            disc.competencies = await _load_competencies(db, update_data.pop("competency_ids"))
        for field, value in update_data.items():
            setattr(disc, field, value)
        await db.flush()
        return disc

    async def delete(self, discipline_id: uuid.UUID, db: AsyncSession) -> None:
        disc = await self.get(discipline_id, db)
        await db.delete(disc)
        await db.flush()


# ── Программы ЦК ─────────────────────────────────────────────────────────────


class CKCourseService:
    async def list(self, db: AsyncSession, *, offset: int = 0, limit: int = 50) -> list[CKCourse]:
        result = await db.execute(
            select(CKCourse)
            .options(selectinload(CKCourse.competencies), selectinload(CKCourse.prerequisites))
            .order_by(CKCourse.category, CKCourse.name)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get(self, course_id: uuid.UUID, db: AsyncSession) -> CKCourse:
        result = await db.execute(
            select(CKCourse)
            .options(selectinload(CKCourse.competencies), selectinload(CKCourse.prerequisites))
            .where(CKCourse.id == course_id)
        )
        course = result.scalar_one_or_none()
        if course is None:
            raise NotFoundError("CKCourse", str(course_id))
        return course

    async def create(self, data: CKCourseCreate, db: AsyncSession) -> CKCourse:
        comps = await _load_competencies(db, data.competency_ids)
        prereqs = await _load_competencies(db, data.prerequisite_ids)
        course = CKCourse(
            name=data.name, description=data.description,
            category=data.category, credits=data.credits,
        )
        course.competencies = comps
        course.prerequisites = prereqs
        db.add(course)
        await db.flush()
        return course

    async def update(
        self, course_id: uuid.UUID, data: CKCourseUpdate, db: AsyncSession
    ) -> CKCourse:
        course = await self.get(course_id, db)
        update_data = data.model_dump(exclude_unset=True)
        if "competency_ids" in update_data:
            course.competencies = await _load_competencies(db, update_data.pop("competency_ids"))
        if "prerequisite_ids" in update_data:
            course.prerequisites = await _load_competencies(
                db, update_data.pop("prerequisite_ids")
            )
        for field, value in update_data.items():
            setattr(course, field, value)
        await db.flush()
        return course

    async def delete(self, course_id: uuid.UUID, db: AsyncSession) -> None:
        course = await self.get(course_id, db)
        await db.delete(course)
        await db.flush()


# ── Карьерные направления ────────────────────────────────────────────────────


class CareerDirectionService:
    async def list(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 50
    ) -> list[CareerDirection]:
        result = await db.execute(
            select(CareerDirection)
            .options(selectinload(CareerDirection.competencies))
            .order_by(CareerDirection.name)
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().unique().all())

    async def get(self, direction_id: uuid.UUID, db: AsyncSession) -> CareerDirection:
        result = await db.execute(
            select(CareerDirection)
            .options(selectinload(CareerDirection.competencies))
            .where(CareerDirection.id == direction_id)
        )
        direction = result.scalar_one_or_none()
        if direction is None:
            raise NotFoundError("CareerDirection", str(direction_id))
        return direction

    async def create(self, data: CareerDirectionCreate, db: AsyncSession) -> CareerDirection:
        comps = await _load_competencies(db, data.competency_ids)
        direction = CareerDirection(
            name=data.name, description=data.description, example_jobs=data.example_jobs
        )
        direction.competencies = comps
        db.add(direction)
        await db.flush()
        return direction

    async def update(
        self, direction_id: uuid.UUID, data: CareerDirectionUpdate, db: AsyncSession
    ) -> CareerDirection:
        direction = await self.get(direction_id, db)
        update_data = data.model_dump(exclude_unset=True)
        if "competency_ids" in update_data:
            direction.competencies = await _load_competencies(
                db, update_data.pop("competency_ids")
            )
        for field, value in update_data.items():
            setattr(direction, field, value)
        await db.flush()
        return direction

    async def delete(self, direction_id: uuid.UUID, db: AsyncSession) -> None:
        direction = await self.get(direction_id, db)
        await db.delete(direction)
        await db.flush()


# ── Таблица фокусов ─────────────────────────────────────────────────────────


class FocusAdviceService:
    async def list(
        self, db: AsyncSession, *, offset: int = 0, limit: int = 50
    ) -> list[FocusAdvice]:
        result = await db.execute(
            select(FocusAdvice).order_by(FocusAdvice.discipline_id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, advice_id: uuid.UUID, db: AsyncSession) -> FocusAdvice:
        result = await db.execute(select(FocusAdvice).where(FocusAdvice.id == advice_id))
        advice = result.scalar_one_or_none()
        if advice is None:
            raise NotFoundError("FocusAdvice", str(advice_id))
        return advice

    async def create(self, data: FocusAdviceCreate, db: AsyncSession) -> FocusAdvice:
        advice = FocusAdvice(
            discipline_id=data.discipline_id,
            career_direction_id=data.career_direction_id,
            focus_advice=data.focus_advice,
            reasoning=data.reasoning,
        )
        db.add(advice)
        await db.flush()
        return advice

    async def update(
        self, advice_id: uuid.UUID, data: FocusAdviceUpdate, db: AsyncSession
    ) -> FocusAdvice:
        advice = await self.get(advice_id, db)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(advice, field, value)
        await db.flush()
        return advice

    async def delete(self, advice_id: uuid.UUID, db: AsyncSession) -> None:
        advice = await self.get(advice_id, db)
        await db.delete(advice)
        await db.flush()


# ── Правила ЭС ──────────────────────────────────────────────────────────────


class RuleService:
    async def list(self, db: AsyncSession, *, offset: int = 0, limit: int = 100) -> list[Rule]:
        result = await db.execute(select(Rule).order_by(Rule.number).offset(offset).limit(limit))
        return list(result.scalars().all())

    async def get(self, rule_id: uuid.UUID, db: AsyncSession) -> Rule:
        result = await db.execute(select(Rule).where(Rule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule is None:
            raise NotFoundError("Rule", str(rule_id))
        return rule

    async def create(self, data: RuleCreate, db: AsyncSession) -> Rule:
        rule = Rule(
            number=data.number,
            group=data.group,
            name=data.name,
            description=data.description,
            condition=data.condition,
            recommendation=data.recommendation,
            priority=data.priority,
            is_active=data.is_active,
        )
        db.add(rule)
        await db.flush()
        return rule

    async def update(self, rule_id: uuid.UUID, data: RuleUpdate, db: AsyncSession) -> Rule:
        rule = await self.get(rule_id, db)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(rule, field, value)
        await db.flush()
        return rule

    async def delete(self, rule_id: uuid.UUID, db: AsyncSession) -> None:
        rule = await self.get(rule_id, db)
        await db.delete(rule)
        await db.flush()

    async def set_published(
        self, rule_id: uuid.UUID, published: bool, db: AsyncSession
    ) -> Rule:
        """Перевод правила между статусами draft и published."""
        rule = await self.get(rule_id, db)
        rule.is_published = published
        await db.flush()
        return rule


# ── Управление пользователями ──────────────────────────────────────────────


class UserAdminService:
    """CRUD пользователей для администратора."""

    async def list(self, db: AsyncSession, *, offset: int = 0, limit: int = 50) -> list[User]:
        result = await db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, user_id: uuid.UUID, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User", str(user_id))
        return user

    async def update(
        self, user_id: uuid.UUID, data: UserAdminUpdate, db: AsyncSession
    ) -> User:
        user = await self.get(user_id, db)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        await db.flush()
        return user


# ── Синглтоны сервисов ───────────────────────────────────────────────────────

competency_service = CompetencyService()
discipline_service = DisciplineService()
ck_course_service = CKCourseService()
career_direction_service = CareerDirectionService()
focus_advice_service = FocusAdviceService()
rule_service = RuleService()
user_admin_service = UserAdminService()
