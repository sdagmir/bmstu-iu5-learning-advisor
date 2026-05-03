"""Фикстуры для integration-тестов.

Особенности:
- Перед любым импортом app подменяем DATABASE_URL на тестовую БД (rs_ito_test).
- Глобальные `engine` и `async_session_factory` подменяются на тестовые с NullPool —
  без долгоживущих connections, что избавляет от teardown-граблей pytest-asyncio.
- Схема создаётся один раз на сессию, перед каждым тестом таблицы очищаются TRUNCATE.
- LLM и embedder подменяются на фейки в `chat_service` / `rag_service`.
- HTTP-клиент — `httpx.AsyncClient` с `ASGITransport`, без поднятия uvicorn.
"""

from __future__ import annotations

import os

# КРИТИЧНО: подмена URL до любых импортов из app.* — иначе settings подхватит prod БД
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://rs_ito:rs_ito@postgres:5432/rs_ito_test"
)

import uuid  # noqa: E402
from collections.abc import AsyncIterator  # noqa: E402
from typing import Any  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

import app.db.database as db_module  # noqa: E402
from app.config import settings  # noqa: E402

# Создаём тестовый engine с NullPool (никаких долгоживущих connections)
# и подменяем глобальные ссылки до того, как другие модули импортируют их
_test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)
_test_session_factory = async_sessionmaker(
    _test_engine, class_=AsyncSession, expire_on_commit=False
)
db_module.engine = _test_engine
db_module.async_session_factory = _test_session_factory

from app.auth.security import hash_password  # noqa: E402
from app.db.models import (  # noqa: E402
    Base,
    CareerGoal,
    TechparkStatus,
    User,
    UserRole,
    WorkloadPref,
)
from app.llm.service import chat_service  # noqa: E402
from app.main import create_app  # noqa: E402
from app.rag.service import rag_service  # noqa: E402

# Модули, которые импортировали async_session_factory напрямую, держат старую ссылку —
# подменяем явно
import app.admin.seed as _admin_seed  # noqa: E402
import app.llm.router as _llm_router  # noqa: E402

_llm_router.async_session_factory = _test_session_factory
_admin_seed.async_session_factory = _test_session_factory

from tests.integration._fakes import FakeEmbeddingClient, FakeLLMClient  # noqa: E402


# ── Schema lifecycle ──────────────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="session", autouse=True, loop_scope="session")
async def _setup_schema() -> AsyncIterator[None]:
    """Один раз на сессию: пересоздать схему тестовой БД с нуля."""
    async with _test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # При NullPool нет открытых connections — dispose безопасен
    await _test_engine.dispose()


# Таблицы с пользовательскими данными — стираются перед каждым тестом
_USER_TABLES = (
    "refresh_tokens",
    "student_completed_ck",
    "student_grades",
    "focus_advices",
    "rule_editing_locks",
    "users",
)
# Таблицы с seed-данными — стираются только в `_full_clean` (когда нужно загрузить заново)
_SEED_TABLES = (
    "discipline_competencies",
    "ck_course_competencies",
    "ck_course_prerequisites",
    "career_competencies",
    "rules",
    "disciplines",
    "ck_courses",
    "career_directions",
    "competencies",
)


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _clean_user_tables() -> AsyncIterator[None]:
    """Перед каждым тестом — TRUNCATE пользовательских таблиц для изоляции."""
    names = ", ".join(f'"{t}"' for t in _USER_TABLES)
    async with _test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {names} RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture(loop_scope="session")
async def seeded() -> None:
    """Загружает seed-данные (компетенции, дисциплины, ЦК, направления, правила).

    Идемпотентна на уровне сессии: первый вызов чистит и загружает, последующие —
    проверяют что данные уже есть. Используй когда тесту нужны реальные данные seed.
    """
    from app.admin.seed import run_seed

    # Если seed-таблицы уже наполнены — пропустить
    async with _test_session_factory() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM competencies"))
        count = result.scalar_one()
    if count > 0:
        return

    await run_seed()


# ── Fakes для внешних зависимостей ────────────────────────────────────────────


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    """Фейк OpenRouter — заменяет httpx-клиент в chat_service на время теста."""
    fake = FakeLLMClient()
    original = chat_service._llm
    chat_service._llm = fake  # type: ignore[assignment]
    yield fake
    chat_service._llm = original


@pytest.fixture
def fake_embedder() -> FakeEmbeddingClient:
    """Фейк эмбеддера — заменяет httpx-клиент в rag_service."""
    fake = FakeEmbeddingClient()
    original = rag_service._embedder
    rag_service._embedder = fake  # type: ignore[assignment]
    yield fake
    rag_service._embedder = original


# ── HTTP-клиент ──────────────────────────────────────────────────────────────


@pytest_asyncio.fixture(loop_scope="session")
async def client() -> AsyncIterator[AsyncClient]:
    """AsyncClient к FastAPI через ASGI транспорт (без поднятия uvicorn)."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Прямой доступ к БД (для arrange-фазы тестов) ──────────────────────────────


@pytest_asyncio.fixture(loop_scope="session")
async def db() -> AsyncIterator[AsyncSession]:
    """Сессия к тестовой БД для подготовки данных в тестах."""
    async with _test_session_factory() as session:
        yield session


# ── Удобные фикстуры пользователей ────────────────────────────────────────────


async def _create_user(
    db: AsyncSession,
    *,
    email: str,
    password: str = "Test12345!",
    role: UserRole = UserRole.STUDENT,
    semester: int | None = None,
    career_goal: CareerGoal | None = None,
) -> User:
    user = User(
        id=uuid.uuid4(),
        email=email,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        semester=semester,
        career_goal=career_goal,
        technopark_status=TechparkStatus.NONE,
        workload_pref=WorkloadPref.NORMAL,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture(loop_scope="session")
async def student(db: AsyncSession) -> User:
    """Зарегистрированный студент со стандартным паролем 'Test12345!'."""
    return await _create_user(
        db,
        email="student@example.com",
        semester=4,
        career_goal=CareerGoal.ML,
    )


@pytest_asyncio.fixture(loop_scope="session")
async def admin(db: AsyncSession) -> User:
    """Зарегистрированный админ со стандартным паролем 'Test12345!'."""
    return await _create_user(db, email="admin@example.com", role=UserRole.ADMIN)


async def _login(client: AsyncClient, email: str, password: str = "Test12345!") -> str:
    """Получить access-токен для уже зарегистрированного пользователя."""
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    response.raise_for_status()
    return response.json()["access_token"]


@pytest_asyncio.fixture(loop_scope="session")
async def student_auth(student: User, client: AsyncClient) -> dict[str, str]:
    """Header `Authorization: Bearer <token>` для студента."""
    token = await _login(client, student.email)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(loop_scope="session")
async def admin_auth(admin: User, client: AsyncClient) -> dict[str, str]:
    """Header `Authorization: Bearer <token>` для админа."""
    token = await _login(client, admin.email)
    return {"Authorization": f"Bearer {token}"}


# ── Хелперы ───────────────────────────────────────────────────────────────────


@pytest.fixture
def make_user() -> Any:
    """Фабрика для создания дополнительных пользователей внутри теста."""
    return _create_user
