from __future__ import annotations

from fastapi import APIRouter, status

from app.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.auth.service import auth_service
from app.config import settings
from app.dependencies import DbSession
from app.exceptions import NotFoundError

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: DbSession) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.register(body.email, body.password, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: DbSession) -> TokenResponse:
    _, access_token, refresh_token = await auth_service.login(body.email, body.password, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/demo-login", response_model=TokenResponse)
async def demo_login(db: DbSession) -> TokenResponse:
    """Один клик — токены для демо-аккаунта (для защиты диплома).

    Активен только при `DEMO_ACCOUNT_ENABLED=true` в окружении. На проде
    отдаёт 404 — фронт может показывать кнопку всегда и тихо обрабатывать ошибку.
    """
    if not settings.demo_account_enabled:
        raise NotFoundError("Endpoint", "demo-login")
    _, access_token, refresh_token = await auth_service.login(
        settings.demo_account_email, settings.demo_account_password, db
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DbSession) -> TokenResponse:
    access_token, refresh_token = await auth_service.refresh(body.refresh_token, db)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: DbSession) -> None:
    await auth_service.logout(body.refresh_token, db)
