from __future__ import annotations

from fastapi import APIRouter

from app.dependencies import CurrentUser, DbSession
from app.users.schemas import ProfileUpdate, UserRead
from app.users.service import user_service

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def get_me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)


@router.patch("/me", response_model=UserRead)
async def update_profile(body: ProfileUpdate, user: CurrentUser, db: DbSession) -> UserRead:
    updated = await user_service.update_profile(user, body, db)
    return UserRead.model_validate(updated)
