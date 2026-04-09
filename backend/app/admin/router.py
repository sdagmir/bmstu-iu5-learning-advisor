"""Роутер админки — CRUD для всех сущностей. Все эндпоинты требуют роль admin."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from app.admin.schemas import (
    CareerDirectionCreate,
    CareerDirectionRead,
    CareerDirectionUpdate,
    CKCourseCreate,
    CKCourseRead,
    CKCourseUpdate,
    CompetencyCreate,
    CompetencyRead,
    CompetencyUpdate,
    DisciplineCreate,
    DisciplineRead,
    DisciplineUpdate,
    FocusAdviceCreate,
    FocusAdviceRead,
    FocusAdviceUpdate,
    RuleCreate,
    RuleRead,
    RuleUpdate,
    UserAdminRead,
    UserAdminUpdate,
)
from app.admin.service import (
    career_direction_service,
    ck_course_service,
    competency_service,
    discipline_service,
    focus_advice_service,
    rule_service,
    user_admin_service,
)
from app.dependencies import CurrentAdmin, DbSession, PageLimit, PageOffset

router = APIRouter()


# ── Пользователи ────────────────────────────────────────────────────────────


@router.get("/users", response_model=list[UserAdminRead])
async def list_users(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[UserAdminRead]:
    items = await user_admin_service.list(db, offset=offset, limit=limit)
    return [UserAdminRead.model_validate(i) for i in items]


@router.get("/users/{user_id}", response_model=UserAdminRead)
async def get_user(user_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> UserAdminRead:
    user = await user_admin_service.get(user_id, db)
    return UserAdminRead.model_validate(user)


@router.patch("/users/{user_id}", response_model=UserAdminRead)
async def update_user(
    user_id: uuid.UUID, body: UserAdminUpdate, admin: CurrentAdmin, db: DbSession
) -> UserAdminRead:
    user = await user_admin_service.update(user_id, body, db)
    return UserAdminRead.model_validate(user)


# ── Компетенции ──────────────────────────────────────────────────────────────


@router.get("/competencies", response_model=list[CompetencyRead])
async def list_competencies(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[CompetencyRead]:
    items = await competency_service.list(db, offset=offset, limit=limit)
    return [CompetencyRead.model_validate(i) for i in items]


@router.post("/competencies", response_model=CompetencyRead, status_code=201)
async def create_competency(
    body: CompetencyCreate, admin: CurrentAdmin, db: DbSession
) -> CompetencyRead:
    item = await competency_service.create(body, db)
    return CompetencyRead.model_validate(item)


@router.patch("/competencies/{competency_id}", response_model=CompetencyRead)
async def update_competency(
    competency_id: uuid.UUID, body: CompetencyUpdate, admin: CurrentAdmin, db: DbSession
) -> CompetencyRead:
    item = await competency_service.update(competency_id, body, db)
    return CompetencyRead.model_validate(item)


@router.delete("/competencies/{competency_id}", status_code=204)
async def delete_competency(competency_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> None:
    await competency_service.delete(competency_id, db)


# ── Дисциплины ───────────────────────────────────────────────────────────────


@router.get("/disciplines", response_model=list[DisciplineRead])
async def list_disciplines(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[DisciplineRead]:
    items = await discipline_service.list(db, offset=offset, limit=limit)
    return [DisciplineRead.model_validate(i) for i in items]


@router.post("/disciplines", response_model=DisciplineRead, status_code=201)
async def create_discipline(
    body: DisciplineCreate, admin: CurrentAdmin, db: DbSession
) -> DisciplineRead:
    item = await discipline_service.create(body, db)
    return DisciplineRead.model_validate(item)


@router.patch("/disciplines/{discipline_id}", response_model=DisciplineRead)
async def update_discipline(
    discipline_id: uuid.UUID, body: DisciplineUpdate, admin: CurrentAdmin, db: DbSession
) -> DisciplineRead:
    item = await discipline_service.update(discipline_id, body, db)
    return DisciplineRead.model_validate(item)


@router.delete("/disciplines/{discipline_id}", status_code=204)
async def delete_discipline(discipline_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> None:
    await discipline_service.delete(discipline_id, db)


# ── Программы ЦК ─────────────────────────────────────────────────────────────


@router.get("/ck-courses", response_model=list[CKCourseRead])
async def list_ck_courses(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[CKCourseRead]:
    items = await ck_course_service.list(db, offset=offset, limit=limit)
    return [CKCourseRead.model_validate(i) for i in items]


@router.post("/ck-courses", response_model=CKCourseRead, status_code=201)
async def create_ck_course(
    body: CKCourseCreate, admin: CurrentAdmin, db: DbSession
) -> CKCourseRead:
    item = await ck_course_service.create(body, db)
    return CKCourseRead.model_validate(item)


@router.patch("/ck-courses/{course_id}", response_model=CKCourseRead)
async def update_ck_course(
    course_id: uuid.UUID, body: CKCourseUpdate, admin: CurrentAdmin, db: DbSession
) -> CKCourseRead:
    item = await ck_course_service.update(course_id, body, db)
    return CKCourseRead.model_validate(item)


@router.delete("/ck-courses/{course_id}", status_code=204)
async def delete_ck_course(course_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> None:
    await ck_course_service.delete(course_id, db)


# ── Карьерные направления ────────────────────────────────────────────────────


@router.get("/career-directions", response_model=list[CareerDirectionRead])
async def list_career_directions(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[CareerDirectionRead]:
    items = await career_direction_service.list(db, offset=offset, limit=limit)
    return [CareerDirectionRead.model_validate(i) for i in items]


@router.post("/career-directions", response_model=CareerDirectionRead, status_code=201)
async def create_career_direction(
    body: CareerDirectionCreate, admin: CurrentAdmin, db: DbSession
) -> CareerDirectionRead:
    item = await career_direction_service.create(body, db)
    return CareerDirectionRead.model_validate(item)


@router.patch("/career-directions/{direction_id}", response_model=CareerDirectionRead)
async def update_career_direction(
    direction_id: uuid.UUID, body: CareerDirectionUpdate, admin: CurrentAdmin, db: DbSession
) -> CareerDirectionRead:
    item = await career_direction_service.update(direction_id, body, db)
    return CareerDirectionRead.model_validate(item)


@router.delete("/career-directions/{direction_id}", status_code=204)
async def delete_career_direction(
    direction_id: uuid.UUID, admin: CurrentAdmin, db: DbSession
) -> None:
    await career_direction_service.delete(direction_id, db)


# ── Таблица фокусов ─────────────────────────────────────────────────────────


@router.get("/focus-advices", response_model=list[FocusAdviceRead])
async def list_focus_advices(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 50
) -> list[FocusAdviceRead]:
    items = await focus_advice_service.list(db, offset=offset, limit=limit)
    return [FocusAdviceRead.model_validate(i) for i in items]


@router.post("/focus-advices", response_model=FocusAdviceRead, status_code=201)
async def create_focus_advice(
    body: FocusAdviceCreate, admin: CurrentAdmin, db: DbSession
) -> FocusAdviceRead:
    item = await focus_advice_service.create(body, db)
    return FocusAdviceRead.model_validate(item)


@router.patch("/focus-advices/{advice_id}", response_model=FocusAdviceRead)
async def update_focus_advice(
    advice_id: uuid.UUID, body: FocusAdviceUpdate, admin: CurrentAdmin, db: DbSession
) -> FocusAdviceRead:
    item = await focus_advice_service.update(advice_id, body, db)
    return FocusAdviceRead.model_validate(item)


@router.delete("/focus-advices/{advice_id}", status_code=204)
async def delete_focus_advice(advice_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> None:
    await focus_advice_service.delete(advice_id, db)


# ── Правила ЭС ──────────────────────────────────────────────────────────────


@router.get("/rules", response_model=list[RuleRead])
async def list_rules(
    admin: CurrentAdmin, db: DbSession, offset: PageOffset = 0, limit: PageLimit = 100
) -> list[RuleRead]:
    items = await rule_service.list(db, offset=offset, limit=limit)
    return [RuleRead.model_validate(i) for i in items]


@router.post("/rules", response_model=RuleRead, status_code=201)
async def create_rule(body: RuleCreate, admin: CurrentAdmin, db: DbSession) -> RuleRead:
    item = await rule_service.create(body, db)
    return RuleRead.model_validate(item)


@router.patch("/rules/{rule_id}", response_model=RuleRead)
async def update_rule(
    rule_id: uuid.UUID, body: RuleUpdate, admin: CurrentAdmin, db: DbSession
) -> RuleRead:
    item = await rule_service.update(rule_id, body, db)
    return RuleRead.model_validate(item)


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: uuid.UUID, admin: CurrentAdmin, db: DbSession) -> None:
    await rule_service.delete(rule_id, db)
