from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.config import settings
from app.db.models import RefreshToken, User, UserRole
from app.exceptions import ConflictError, UnauthorizedError

# Фиктивный хэш для timing-safe сравнения, когда пользователь не найден
_DUMMY_HASH = "$2b$12$" + "0" * 53


class AuthService:
    async def register(
        self, email: str, password: str, db: AsyncSession, *, role: UserRole = UserRole.STUDENT
    ) -> tuple[User, str, str]:
        """Регистрация пользователя. Возвращает (user, access_token, refresh_token)."""
        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        db.add(user)
        try:
            await db.flush()
        except IntegrityError as exc:
            await db.rollback()
            raise ConflictError(f"User with email '{email}' already exists") from exc

        # Выпуск токенов сразу (без повторного bcrypt)
        access_token = create_access_token(str(user.id), user.role.value)
        raw_refresh, refresh_hash = create_refresh_token()

        token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_token_ttl),
        )
        db.add(token)
        await db.flush()

        return user, access_token, raw_refresh

    async def login(self, email: str, password: str, db: AsyncSession) -> tuple[User, str, str]:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        # Timing-safe: всегда вызываем verify_password для защиты от перебора email
        stored_hash = user.password_hash if user is not None else _DUMMY_HASH
        password_valid = verify_password(password, stored_hash)

        if user is None or not password_valid:
            raise UnauthorizedError("Invalid email or password")
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        access_token = create_access_token(str(user.id), user.role.value)
        raw_refresh, refresh_hash = create_refresh_token()

        token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_token_ttl),
        )
        db.add(token)
        await db.flush()

        return user, access_token, raw_refresh

    async def refresh(self, raw_token: str, db: AsyncSession) -> tuple[str, str]:
        token_hash = hash_refresh_token(raw_token)
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        token = result.scalar_one_or_none()
        if token is None:
            raise UnauthorizedError("Invalid or expired refresh token")

        # Отзыв старого токена
        token.is_revoked = True

        # Загрузка пользователя и проверка активности
        user_result = await db.execute(select(User).where(User.id == token.user_id))
        user = user_result.scalar_one()
        if not user.is_active:
            raise UnauthorizedError("Account is deactivated")

        # Выпуск новой пары токенов
        new_access = create_access_token(str(user.id), user.role.value)
        new_raw, new_hash = create_refresh_token()

        new_token = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.jwt_refresh_token_ttl),
        )
        db.add(new_token)
        await db.flush()

        return new_access, new_raw

    async def logout(self, raw_token: str, db: AsyncSession) -> None:
        token_hash = hash_refresh_token(raw_token)
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        token = result.scalar_one_or_none()
        if token is not None:
            token.is_revoked = True
            await db.flush()


auth_service = AuthService()
