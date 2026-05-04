from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ── Перечисления ─────────────────────────────────────────────────────────────


class UserRole(enum.StrEnum):
    STUDENT = "student"
    ADMIN = "admin"


class CareerGoal(enum.StrEnum):
    ML = "ml"
    BACKEND = "backend"
    FRONTEND = "frontend"
    CYBERSECURITY = "cybersecurity"
    SYSTEM = "system"
    DEVOPS = "devops"
    MOBILE = "mobile"
    GAMEDEV = "gamedev"
    QA = "qa"
    ANALYTICS = "analytics"
    UNDECIDED = "undecided"


class TechparkStatus(enum.StrEnum):
    NONE = "none"
    BACKEND = "backend"
    FRONTEND = "frontend"
    ML = "ml"
    MOBILE = "mobile"


class WorkloadPref(enum.StrEnum):
    LIGHT = "light"
    NORMAL = "normal"
    INTENSIVE = "intensive"


class CompetencyCategory(enum.StrEnum):
    PROGRAMMING = "programming"
    MATH = "math"
    DATA = "data"
    ML = "ml"
    ENGINEERING = "engineering"
    NETWORKS = "networks"
    SYSTEM = "system"
    APPLIED = "applied"


class DisciplineType(enum.StrEnum):
    MANDATORY = "mandatory"
    ELECTIVE = "elective"
    CHOICE = "choice"


class CKCourseCategory(enum.StrEnum):
    ML = "ml"
    DEVELOPMENT = "development"
    SECURITY = "security"
    TESTING = "testing"
    MANAGEMENT = "management"
    OTHER = "other"


class RuleGroup(enum.StrEnum):
    CK_PROGRAMS = "ck_programs"
    BASIC_UNIVERSAL = "basic_universal"
    TECHNOPARK = "technopark"
    DISCIPLINE_FOCUS = "discipline_focus"
    COURSEWORK = "coursework"
    WARNINGS = "warnings"
    STRATEGY = "strategy"


class RecommendationCategory(enum.StrEnum):
    CK_COURSE = "ck_course"
    TECHNOPARK = "technopark"
    FOCUS = "focus"
    COURSEWORK = "coursework"
    WARNING = "warning"
    STRATEGY = "strategy"


class RecommendationPriority(enum.StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# ── Базовый класс ────────────────────────────────────────────────────────────


class Base(DeclarativeBase):
    pass


# ── Связующие таблицы (M:N) ──────────────────────────────────────────────────


discipline_competencies = Table(
    "discipline_competencies",
    Base.metadata,
    Column("discipline_id", UUID(as_uuid=True), ForeignKey("disciplines.id"), primary_key=True),
    Column("competency_id", UUID(as_uuid=True), ForeignKey("competencies.id"), primary_key=True),
)

ck_course_competencies = Table(
    "ck_course_competencies",
    Base.metadata,
    Column("ck_course_id", UUID(as_uuid=True), ForeignKey("ck_courses.id"), primary_key=True),
    Column("competency_id", UUID(as_uuid=True), ForeignKey("competencies.id"), primary_key=True),
)

ck_course_prerequisites = Table(
    "ck_course_prerequisites",
    Base.metadata,
    Column("ck_course_id", UUID(as_uuid=True), ForeignKey("ck_courses.id"), primary_key=True),
    Column("competency_id", UUID(as_uuid=True), ForeignKey("competencies.id"), primary_key=True),
)

career_competencies = Table(
    "career_competencies",
    Base.metadata,
    Column(
        "career_direction_id",
        UUID(as_uuid=True),
        ForeignKey("career_directions.id"),
        primary_key=True,
    ),
    Column("competency_id", UUID(as_uuid=True), ForeignKey("competencies.id"), primary_key=True),
)


# ── Модели ───────────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.STUDENT)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Поля профиля студента (nullable для админов)
    semester: Mapped[int | None] = mapped_column(Integer)
    career_goal: Mapped[CareerGoal | None] = mapped_column(Enum(CareerGoal))
    technopark_status: Mapped[TechparkStatus | None] = mapped_column(
        Enum(TechparkStatus), default=TechparkStatus.NONE
    )
    workload_pref: Mapped[WorkloadPref | None] = mapped_column(
        Enum(WorkloadPref), default=WorkloadPref.NORMAL
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Связи
    refresh_tokens: Mapped[list[RefreshToken]] = relationship(back_populates="user")
    completed_ck: Mapped[list[StudentCompletedCK]] = relationship(back_populates="user")
    grades: Mapped[list[StudentGrade]] = relationship(back_populates="user")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="refresh_tokens")


class Competency(Base):
    __tablename__ = "competencies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[CompetencyCategory] = mapped_column(Enum(CompetencyCategory))

    # Связи
    disciplines: Mapped[list[Discipline]] = relationship(
        secondary=discipline_competencies, back_populates="competencies"
    )
    ck_courses: Mapped[list[CKCourse]] = relationship(
        secondary=ck_course_competencies, back_populates="competencies"
    )
    career_directions: Mapped[list[CareerDirection]] = relationship(
        secondary=career_competencies, back_populates="competencies"
    )


class Discipline(Base):
    __tablename__ = "disciplines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    semester: Mapped[int] = mapped_column(Integer)
    credits: Mapped[int] = mapped_column(Integer)
    type: Mapped[DisciplineType] = mapped_column(Enum(DisciplineType))
    control_form: Mapped[str] = mapped_column(String(50))
    department: Mapped[str | None] = mapped_column(String(50))

    # Связи
    competencies: Mapped[list[Competency]] = relationship(
        secondary=discipline_competencies, back_populates="disciplines"
    )
    focus_advices: Mapped[list[FocusAdvice]] = relationship(back_populates="discipline")


class CKCourse(Base):
    __tablename__ = "ck_courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[CKCourseCategory] = mapped_column(Enum(CKCourseCategory))
    credits: Mapped[int] = mapped_column(Integer, default=2)  # е.з., по умолчанию 2

    # Связи
    competencies: Mapped[list[Competency]] = relationship(
        secondary=ck_course_competencies, back_populates="ck_courses"
    )
    prerequisites: Mapped[list[Competency]] = relationship(secondary=ck_course_prerequisites)


class CareerDirection(Base):
    __tablename__ = "career_directions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    example_jobs: Mapped[str | None] = mapped_column(Text)

    # Связи
    competencies: Mapped[list[Competency]] = relationship(
        secondary=career_competencies, back_populates="career_directions"
    )
    focus_advices: Mapped[list[FocusAdvice]] = relationship(back_populates="career_direction")


class Rule(Base):
    """Правило экспертной системы. Хранит условия и рекомендацию в JSON.

    Жизненный цикл:
    - is_active=False — правило выключено, движок его игнорирует (kill-switch)
    - is_active=True, is_published=False — черновик, виден только в админ-preview
    - is_active=True, is_published=True — опубликовано, применяется ко всем студентам
    """

    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    number: Mapped[int] = mapped_column(Integer, unique=True)
    group: Mapped[RuleGroup] = mapped_column(Enum(RuleGroup))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    condition: Mapped[dict] = mapped_column(JSON)
    recommendation: Mapped[dict] = mapped_column(JSON)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    # Опубликованное правило применяется к рекомендациям всех студентов.
    # Новое правило по умолчанию — черновик; админ публикует через эндпоинт.
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    # Сколько раз правило сработало в production-движке (только /my-recommendations).
    # Не растёт для preview/sandbox/what-if вызовов.
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class RuleEditingLock(Base):
    """Pessimistic-лок на редактирование правил.

    Singleton-таблица: одна запись с slot=1 одновременно. Когда админ начинает
    работу с конструктором, он захватывает лок; пока лок активен, mutating-операции
    над правилами доступны только этому админу. Лок имеет TTL (по умолчанию 30 мин)
    и автоматически освобождается, если админ его не продлил.
    """

    __tablename__ = "rule_editing_locks"

    slot: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    admin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    acquired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FocusAdvice(Base):
    __tablename__ = "focus_advices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("disciplines.id", ondelete="CASCADE")
    )
    career_direction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("career_directions.id", ondelete="CASCADE")
    )
    focus_advice: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str | None] = mapped_column(Text)

    # Связи
    discipline: Mapped[Discipline] = relationship(back_populates="focus_advices")
    career_direction: Mapped[CareerDirection] = relationship(back_populates="focus_advices")

    __table_args__ = (
        UniqueConstraint("discipline_id", "career_direction_id", name="uq_focus_disc_career"),
    )


class StudentCompletedCK(Base):
    __tablename__ = "student_completed_ck"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    ck_course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ck_courses.id", ondelete="CASCADE"), primary_key=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="completed_ck")
    ck_course: Mapped[CKCourse] = relationship()


class StudentGrade(Base):
    """Оценка студента по дисциплине. Используется для вычисления X9-X11."""

    __tablename__ = "student_grades"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    discipline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("disciplines.id", ondelete="CASCADE"), primary_key=True
    )
    grade: Mapped[int] = mapped_column(Integer)  # 2-5

    user: Mapped[User] = relationship(back_populates="grades")
    discipline: Mapped[Discipline] = relationship()


class RecommendationHistory(Base):
    """Снимок рекомендаций ЭС в момент значимого изменения профиля.

    Создаётся при изменении X1–X4 (PATCH /users/me) — фиксирует список
    рекомендаций и краткое описание того, что поменялось ("Цель: backend → ml").
    Используется страницей /history для ленты прошлых рекомендаций.
    """

    __tablename__ = "recommendation_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    # JSON-список Recommendation как dict — для устойчивости к изменению схем
    recommendations: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    profile_change_summary: Mapped[str | None] = mapped_column(Text)


class LLMTrace(Base):
    """Журнал запросов к LLM-чату (для админ-страницы /admin/traces).

    Каждый вызов /chat/message и /chat/message/debug пишет запись с request,
    response, отладкой (rules_fired, rag_chunks, tool_calls, profile_changes),
    латентностью и статусом (ok / error / timeout).
    """

    __tablename__ = "llm_traces"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    endpoint: Mapped[str] = mapped_column(String(32), index=True)
    request_message: Mapped[str] = mapped_column(Text)
    response_text: Mapped[str] = mapped_column(Text, default="")
    debug: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16), default="ok", index=True)
    model_name: Mapped[str | None] = mapped_column(String(128))
