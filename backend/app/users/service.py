from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models import User
from app.exceptions import NotFoundError

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.users.schemas import ProfileUpdate


class UserService:
    async def get_by_id(self, user_id: uuid.UUID, db: AsyncSession) -> User:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User", str(user_id))
        return user

    async def update_profile(self, user: User, data: ProfileUpdate, db: AsyncSession) -> User:
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await db.flush()
        return user


user_service = UserService()
