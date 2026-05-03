from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import User
from app.exceptions import ForbiddenError, UnauthorizedError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    from app.auth.security import decode_access_token

    payload = decode_access_token(token)
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or deactivated")
    return user


async def get_current_admin(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    from app.db.models import UserRole

    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Admin access required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentAdmin = Annotated[User, Depends(get_current_admin)]

# Пагинация
PageOffset = Annotated[int, Query(ge=0, description="Смещение (offset)")]
PageLimit = Annotated[int, Query(ge=1, le=100, description="Количество записей")]
