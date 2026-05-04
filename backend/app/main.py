from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    LockedError,
    NotFoundError,
    UnauthorizedError,
    UpstreamError,
    ValidationError,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Инициализация и завершение инфраструктурных клиентов."""
    logger.info("Starting application")

    from app.db.database import async_session_factory
    from app.expert.service import expert_service
    from app.llm.service import chat_service
    from app.rag.service import rag_service

    # Восстановление BM25 корпуса из Qdrant
    try:
        rag_service.restore_bm25_from_qdrant()
    except BaseException:
        logger.warning("Не удалось восстановить BM25, RAG поиск будет без sparse")

    # Загрузка опубликованных правил ЭС из БД (вместо seed in-memory)
    try:
        async with async_session_factory() as db:
            await expert_service.reload_from_db(db)
    except BaseException:
        logger.warning("Не удалось загрузить правила ЭС из БД, движок останется на seed")

    try:
        yield
    finally:
        # Закрытие httpx-клиентов, чтобы не утекали соединения на shutdown
        await chat_service._llm.close()
        await rag_service._embedder.close()
        logger.info("Shutdown complete")


def create_app() -> FastAPI:
    app = FastAPI(
        title="РС ИТО — Backend",
        version="0.1.0",
        description="Рекомендательная система индивидуальной траектории обучения",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        openapi_url="/openapi.json" if settings.debug else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    _register_exception_handlers(app)
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    from app.admin.router import router as admin_router
    from app.auth.router import router as auth_router
    from app.catalog.router import router as catalog_router
    from app.expert.router import router as expert_router
    from app.llm.admin_router import router as llm_admin_router
    from app.llm.router import router as chat_router
    from app.rag.router import router as rag_router
    from app.users.router import router as users_router

    prefix = "/api/v1"
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    app.include_router(catalog_router, prefix=f"{prefix}/catalog", tags=["catalog"])
    app.include_router(expert_router, prefix=f"{prefix}/expert", tags=["expert"])
    app.include_router(chat_router, prefix=f"{prefix}/chat", tags=["chat"])
    app.include_router(rag_router, prefix=f"{prefix}/rag", tags=["rag"])
    app.include_router(admin_router, prefix=f"{prefix}/admin", tags=["admin"])
    app.include_router(llm_admin_router, prefix=f"{prefix}/admin", tags=["admin"])


def _register_exception_handlers(app: FastAPI) -> None:
    status_map: dict[type[AppError], int] = {
        NotFoundError: 404,
        UnauthorizedError: 401,
        ForbiddenError: 403,
        ValidationError: 422,
        ConflictError: 409,
        LockedError: 423,
        UpstreamError: 502,
    }

    for exc_class, status_code in status_map.items():

        def _make_handler(sc: int) -> Any:
            async def handler(request: Request, exc: AppError) -> JSONResponse:
                return JSONResponse(
                    status_code=sc,
                    content={
                        "error": {
                            "code": exc.__class__.__name__,
                            "message": exc.message,
                        }
                    },
                )

            return handler

        app.add_exception_handler(exc_class, _make_handler(status_code))

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        # Дубликаты unique-ключей и нарушения FK на уровне БД → 409
        return JSONResponse(
            status_code=409,
            content={
                "error": {
                    "code": "ConflictError",
                    "message": "Resource already exists or violates a constraint",
                }
            },
        )

    @app.exception_handler(Exception)
    async def catch_all(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "InternalError", "message": "Internal server error"}},
        )


app = create_app()
