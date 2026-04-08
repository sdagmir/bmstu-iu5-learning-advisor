from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.auth.service import AuthService
from app.exceptions import ConflictError, UnauthorizedError


class TestAuthServiceRegister:
    @pytest.mark.asyncio
    async def test_register_creates_user_and_tokens(self, mock_db: AsyncMock) -> None:
        service = AuthService()
        mock_db.flush = AsyncMock()

        user, access_token, refresh_token = await service.register(
            "new@test.com", "password123", mock_db
        )

        assert user.email == "new@test.com"
        assert user.password_hash != "password123"
        assert isinstance(access_token, str)
        assert isinstance(refresh_token, str)
        assert len(access_token) > 0
        assert len(refresh_token) > 0

    @pytest.mark.asyncio
    async def test_register_duplicate_raises(self, mock_db: AsyncMock) -> None:
        service = AuthService()

        # Имитация IntegrityError при flush (защита от race condition)
        mock_db.flush = AsyncMock(
            side_effect=IntegrityError("", params=None, orig=Exception("duplicate"))
        )
        mock_db.rollback = AsyncMock()

        with pytest.raises(ConflictError, match="already exists"):
            await service.register("existing@test.com", "password123", mock_db)


class TestAuthServiceLogin:
    @pytest.mark.asyncio
    async def test_login_invalid_email_raises(self, mock_db: AsyncMock) -> None:
        service = AuthService()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(UnauthorizedError, match="Invalid email or password"):
            await service.login("nobody@test.com", "password", mock_db)

    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(
        self, mock_db: AsyncMock, mock_user: MagicMock
    ) -> None:
        service = AuthService()
        mock_user.is_active = False
        from app.auth.security import hash_password

        mock_user.password_hash = hash_password("password123")

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(UnauthorizedError, match="deactivated"):
            await service.login("student@test.com", "password123", mock_db)
