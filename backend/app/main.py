from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
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
    yield
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
    from app.auth.router import router as auth_router
    from app.expert.router import router as expert_router
    from app.users.router import router as users_router

    prefix = "/api/v1"
    app.include_router(auth_router, prefix=f"{prefix}/auth", tags=["auth"])
    app.include_router(users_router, prefix=f"{prefix}/users", tags=["users"])
    app.include_router(expert_router, prefix=f"{prefix}/expert", tags=["expert"])


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

    @app.exception_handler(Exception)
    async def catch_all(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "InternalError", "message": "Internal server error"}},
        )


app = create_app()
