---
name: backend
description: "Build backend with Python 3.12 + FastAPI + SQLAlchemy + Qdrant + OpenRouter. Battle-tested patterns from production. Use when creating/modifying any backend code, setting up project infrastructure, adding modules, or fixing issues."
---

# Diploma Backend — Python 3.12 + FastAPI + OpenRouter + Qdrant

## Identity

You are a senior Python backend engineer building a diploma project backend.
You produce clean, working code from the first attempt. Every pattern below
is battle-tested in production. Follow them EXACTLY — do not improvise
infrastructure code.

---

## Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Runtime | Python | 3.12+ |
| Framework | FastAPI | 0.115+ |
| ORM | SQLAlchemy 2.x (async) | 2.0+ |
| DB | PostgreSQL | 15+ |
| Vector DB | Qdrant | latest |
| LLM | OpenRouter API (OpenAI-compatible) | — |
| Auth | JWT (python-jose) + bcrypt (passlib) | — |
| Migrations | Alembic | 1.13+ |
| HTTP client | httpx (async) | 0.27+ |
| Validation | Pydantic v2 | 2.7+ |
| Settings | pydantic-settings | 2.0+ |
| Testing | pytest + pytest-asyncio | — |
| Linting | ruff | 0.6+ |
| Types | mypy (strict) | 1.11+ |
| Containers | Docker + docker-compose | — |

---

## Project Structure

```
project-root/
├── app/
│   ├── __init__.py
│   ├── main.py              # create_app(), lifespan, routers
│   ├── config.py             # Settings (pydantic-settings)
│   ├── exceptions.py         # Domain exceptions → HTTP codes
│   ├── dependencies.py       # DI: DbSession, get_current_user, etc.
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py       # async engine + session factory
│   │   ├── models.py         # all ORM models
│   │   └── migrations/       # alembic
│   │       ├── env.py
│   │       └── versions/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── router.py         # register, login, refresh, logout
│   │   ├── service.py        # business logic
│   │   ├── security.py       # JWT + password hashing
│   │   └── schemas.py        # request/response models
│   ├── users/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── llm/                  # LLM Orchestrator module
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py        # chat, streaming, prompt management
│   │   ├── client.py         # OpenRouter httpx client
│   │   └── prompts.py        # system prompts, templates
│   ├── expert/               # Expert System module
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── service.py        # rule engine / Mivar logic
│   │   ├── engine.py         # inference engine core
│   │   └── schemas.py
│   └── rag/                  # RAG Recommendation module
│       ├── __init__.py
│       ├── router.py
│       ├── service.py        # search + rerank + augment
│       ├── embedder.py       # embedding client
│       ├── qdrant_client.py  # vector store operations
│       └── schemas.py
├── tests/
│   ├── conftest.py
│   ├── unit/
│   └── integration/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── alembic.ini
└── README.md
```

---

## Critical Rules (DO NOT SKIP)

### 1. Every file starts with
```python
from __future__ import annotations
```
This enables `str | None` syntax and lazy annotation evaluation. Without it,
forward references break and circular imports appear.

### 2. Never use `except Exception` for async generators
Use `except BaseException` — `CancelledError` is a `BaseException` in Python 3.12.
Missing this causes connection pool leaks when SSE clients disconnect.

### 3. SQLAlchemy async — always set these
```python
engine = create_async_engine(
    url,
    pool_pre_ping=True,      # verify connection alive before use
    pool_recycle=1800,        # replace stale connections after 30min
    echo=debug,
    future=True,
)
session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,   # CRITICAL: prevents lazy-load errors in async
)
```

### 4. DB session generator — catch BaseException
```python
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
```

### 5. Never pass `db: AsyncSession` to async generators (SSE/streaming)
The generator outlives the request → session returned to pool → pool leak.
Instead, create a short-lived session inside the generator:
```python
async def stream():
    async with async_session_factory() as db:
        # short query
        ...
    yield data
```

### 6. Refresh tokens — NEVER store raw
Store `SHA-256(token)` in DB. Return raw token to client. On refresh, hash
the incoming token and compare. If DB is compromised, tokens are useless.

### 7. Annotated DI — use type aliases
```python
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
```
This keeps router signatures clean and avoids repeated `Depends()`.

### 8. Router → Service separation
Router: HTTP layer (parse request, rate limit, auth check, return response).
Service: Business logic (stateless class, db session injected per method).
Never put business logic in routers. Never import `Request` in services.

### 9. Domain exceptions → HTTP mapping
Define domain exceptions (NotFoundError, ForbiddenError, etc.) and map them
to HTTP codes in a global exception handler. Services throw domain exceptions,
routers never catch them — the handler does.

### 10. Use StrEnum for all enums
```python
class UserRole(enum.StrEnum):
    USER = "user"
    ADMIN = "admin"
```
StrEnum serializes to string automatically in Pydantic and JSON.

---

## File Templates

### pyproject.toml

```toml
[project]
name = "diploma-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "pydantic>=2.7",
    "pydantic-settings>=2.0",
    "python-jose[cryptography]>=3.3",
    "passlib[bcrypt]>=1.7",
    "httpx>=0.27",
    "qdrant-client>=1.9",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.6",
    "mypy>=1.11",
]

[tool.ruff]
line-length = 99
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP", "B", "SIM", "TCH", "RUF", "ASYNC"]
ignore = ["ANN401", "RUF001", "RUF002", "RUF003"]

[tool.ruff.lint.per-file-ignores]
"app/*/router.py" = ["TCH"]
"app/*/schemas.py" = ["TCH"]
"tests/**" = ["ANN"]

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.12"
strict = true
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = ["jose.*", "passlib.*", "qdrant_client.*"]
ignore_missing_imports = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
filterwarnings = [
    "ignore::DeprecationWarning:passlib",
    "ignore::DeprecationWarning:jose",
]
```

### .env.example

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/diploma

# Auth
JWT_SECRET_KEY=change-me-to-at-least-32-characters-long-secret
JWT_ACCESS_TOKEN_TTL=1800
JWT_REFRESH_TOKEN_TTL=2592000

# LLM (OpenRouter)
LLM_API_KEY=sk-or-v1-your-key
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=google/gemini-2.5-flash

# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents

# Embedding (OpenRouter or dedicated)
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSION=1536

# App
DEBUG=true
CORS_ORIGINS=["http://localhost:3000"]
```

### app/config.py

```python
from __future__ import annotations

import json
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )

    # Database
    database_url: str
    db_pool_size: int = 20

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_ttl: int = 1800
    jwt_refresh_token_ttl: int = 2592000

    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "google/gemini-2.5-flash"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"

    # Embedding
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # App
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, v: str) -> str:
        if len(v) < 32:
            msg = "JWT_SECRET_KEY must be at least 32 characters"
            raise ValueError(msg)
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v

    @property
    def is_production(self) -> bool:
        return not self.debug


settings = Settings()
```

### app/db/database.py

```python
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=10,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=settings.debug,
    future=True,
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except BaseException:
            await session.rollback()
            raise
```

### app/exceptions.py

```python
from __future__ import annotations


class AppError(Exception):
    """Base for all domain errors."""
    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Entity not found. Maps to HTTP 404."""
    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(f"{entity} '{identifier}' not found")


class ForbiddenError(AppError):
    """Access denied. Maps to HTTP 403."""


class ValidationError(AppError):
    """Invalid input. Maps to HTTP 422."""


class ConflictError(AppError):
    """Duplicate or state conflict. Maps to HTTP 409."""


class UnauthorizedError(AppError):
    """Missing or invalid credentials. Maps to HTTP 401."""


class UpstreamError(AppError):
    """External service failure. Maps to HTTP 502."""
    def __init__(self, service: str, detail: str = "") -> None:
        super().__init__(f"{service} unavailable: {detail}")
```

### app/dependencies.py

```python
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.exceptions import UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> "User":
    from app.auth.security import decode_access_token
    from app.db.models import User
    from sqlalchemy import select

    payload = decode_access_token(token)
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")
    return user


CurrentUser = Annotated["User", Depends(get_current_user)]
```

### app/main.py

```python
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    AppError, ConflictError, ForbiddenError,
    NotFoundError, UnauthorizedError, UpstreamError, ValidationError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Initialize and cleanup infrastructure clients."""
    logger.info("Starting application")

    # Qdrant
    try:
        from qdrant_client import QdrantClient
        app.state.qdrant = QdrantClient(url=settings.qdrant_url)
        logger.info("Qdrant connected: %s", settings.qdrant_url)
    except Exception:
        logger.warning("Qdrant unavailable, vector search disabled")
        app.state.qdrant = None

    yield

    # Cleanup
    if app.state.qdrant:
        app.state.qdrant.close()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Diploma Backend",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    _register_exception_handlers(app)

    # Routers
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    from app.auth.router import router as auth_router
    from app.users.router import router as users_router

    prefix = "/api/v1"
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    # Add more routers as modules are built:
    # from app.llm.router import router as llm_router
    # app.include_router(llm_router, prefix=f"{prefix}/chat", tags=["chat"])


def _register_exception_handlers(app: FastAPI) -> None:
    status_map: dict[type[AppError], int] = {
        NotFoundError: 404,
        UnauthorizedError: 401,
        ForbiddenError: 403,
        ValidationError: 422,
        ConflictError: 409,
        UpstreamError: 502,
    }

    for exc_class, status_code in status_map.items():
        app.add_exception_handler(
            exc_class,
            lambda req, exc, sc=status_code: JSONResponse(
                status_code=sc,
                content={"error": {"code": exc.__class__.__name__, "message": exc.message}},
            ),
        )

    @app.exception_handler(Exception)
    async def catch_all(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "InternalError", "message": "Internal server error"}},
        )


app = create_app()
```

### app/auth/security.py

```python
from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import UnauthorizedError

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(seconds=settings.jwt_access_token_ttl),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    return payload


def create_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash). Store hash in DB, return raw to client."""
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
```

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: diploma
      POSTGRES_PASSWORD: diploma
      POSTGRES_DB: diploma
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  app:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      - db
      - qdrant
    volumes:
      - ./app:/code/app

volumes:
  pgdata:
  qdrant_data:
```

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /code
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .

# Run migrations then start
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Module Architecture

### LLM Orchestrator (`app/llm/`)

OpenRouter-compatible client via httpx. Supports streaming (SSE).

```python
# app/llm/client.py — core pattern
class LLMClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self._http = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        self._model = model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """Non-streaming completion."""
        response = await self._http.post("/chat/completions", json={
            "model": self._model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.3),
        })
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    async def stream(self, messages: list[dict], **kwargs):
        """SSE streaming completion. Yields content chunks."""
        async with self._http.stream("POST", "/chat/completions", json={
            "model": self._model,
            "messages": messages,
            "stream": True,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    import json
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if content := delta.get("content"):
                        yield content
```

### Expert System (`app/expert/`)

Rule-based inference. Can be Mivar or Python-native.

```python
# app/expert/engine.py — simple rule engine pattern
@dataclass
class Rule:
    condition: Callable[[dict], bool]
    action: str
    priority: int = 0
    explanation: str = ""

class ExpertEngine:
    def __init__(self, rules: list[Rule]):
        self._rules = sorted(rules, key=lambda r: -r.priority)

    def evaluate(self, facts: dict) -> list[dict]:
        """Fire all matching rules, return actions with explanations."""
        results = []
        for rule in self._rules:
            if rule.condition(facts):
                results.append({
                    "action": rule.action,
                    "explanation": rule.explanation,
                })
        return results
```

### RAG Module (`app/rag/`)

Embed query → Qdrant search → rerank → augment LLM prompt.

```python
# app/rag/service.py — core pattern
class RAGService:
    async def search_and_augment(
        self, query: str, *, top_k: int = 5, db: AsyncSession
    ) -> list[dict]:
        # 1. Embed query
        query_vector = await self._embed(query)

        # 2. Vector search in Qdrant
        hits = self._qdrant.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
        )

        # 3. Fetch full docs from PG
        doc_ids = [hit.payload["document_id"] for hit in hits]
        docs = await self._fetch_docs(doc_ids, db)

        # 4. Build context for LLM
        return [{"content": d.content, "score": h.score} for d, h in zip(docs, hits)]
```

---

## Testing Patterns

### conftest.py

```python
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_db():
    """Mock AsyncSession for unit tests."""
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db

@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "test-user-id"
    user.email = "test@test.com"
    user.role = "user"
    user.is_active = True
    return user
```

### Unit test pattern

```python
class TestSomeService:
    @pytest.mark.asyncio
    async def test_creates_entity(self, mock_db, mock_user) -> None:
        service = SomeService()
        # Mock DB response
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service.create(data, mock_user, mock_db)

        assert result is not None
        mock_db.add.assert_called_once()
```

---

## Common Gotchas & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| `MissingGreenlet` | Lazy load in async context | `expire_on_commit=False` + eager loading |
| Connection pool exhausted | SSE holds session | Never pass `db` to async generators |
| `CancelledError` not caught | `except Exception` doesn't catch it in 3.12 | Use `except BaseException` |
| Circular import | Module A imports from B, B from A | Use `TYPE_CHECKING` + import inside function |
| Pydantic `null` validation fail | API returns `null` for `str` field | `@field_validator(mode="before")` coerce to `""` |
| Alembic can't find models | Not imported before `target_metadata` | `import app.db.models` in `env.py` |
| `asyncpg` won't install | Missing pg_config | `apt-get install libpq-dev` in Dockerfile |
| Token refresh overwrites previous | Raw token stored in DB | Store SHA-256 hash, never raw |
| CORS errors from frontend | Missing `allow_credentials=True` | Add it + explicit origins (no `*`) |

---

## Workflow

1. `docker compose up -d db qdrant` — start infra
2. `cp .env.example .env` — fill secrets
3. `pip install -e ".[dev]"` — install deps
4. `alembic revision --autogenerate -m "initial"` — create migration
5. `alembic upgrade head` — apply
6. `uvicorn app.main:app --reload` — run
7. `pytest tests/` — test
8. `ruff check . && ruff format . && mypy app/` — lint

Build modules in order: **auth → users → llm → rag → expert → integration**.
Each module: models → schemas → service → router → tests.
