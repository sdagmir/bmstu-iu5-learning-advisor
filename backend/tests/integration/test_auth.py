"""Integration-тесты модуля auth: register / login / refresh / logout."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestRegister:
    async def test_register_returns_token_pair(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "StrongPass1!"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["token_type"] == "bearer"
        assert isinstance(data["access_token"], str) and data["access_token"]
        assert isinstance(data["refresh_token"], str) and data["refresh_token"]

    async def test_duplicate_email_returns_409(self, client: AsyncClient) -> None:
        payload = {"email": "dup@example.com", "password": "StrongPass1!"}
        await client.post("/api/v1/auth/register", json=payload)
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 409

    async def test_invalid_email_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "StrongPass1!"},
        )
        assert response.status_code == 422


class TestLogin:
    async def test_login_with_valid_credentials(
        self, client: AsyncClient, student
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": student.email, "password": "Test12345!"},
        )
        assert response.status_code == 200
        assert response.json()["access_token"]

    async def test_login_wrong_password_returns_401(
        self, client: AsyncClient, student
    ) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": student.email, "password": "WrongPassword!"},
        )
        assert response.status_code == 401

    async def test_login_unknown_email_returns_401(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "ghost@example.com", "password": "StrongPass1!"},
        )
        assert response.status_code == 401


class TestRefresh:
    async def test_refresh_rotates_tokens(self, client: AsyncClient, student) -> None:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": student.email, "password": "Test12345!"},
        )
        old_refresh = login.json()["refresh_token"]

        refresh = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert refresh.status_code == 200
        new_refresh = refresh.json()["refresh_token"]
        assert new_refresh != old_refresh

        # старый refresh должен быть отозван
        replay = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert replay.status_code == 401

    async def test_refresh_unknown_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "deadbeef" * 8}
        )
        assert response.status_code == 401


class TestLogout:
    async def test_logout_revokes_refresh(self, client: AsyncClient, student) -> None:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": student.email, "password": "Test12345!"},
        )
        refresh_token = login.json()["refresh_token"]

        logout = await client.post(
            "/api/v1/auth/logout", json={"refresh_token": refresh_token}
        )
        assert logout.status_code == 204

        # refresh после logout невозможен
        replay = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
        )
        assert replay.status_code == 401


class TestProtectedAccess:
    async def test_access_without_token_returns_401(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_access_with_invalid_token_returns_401(
        self, client: AsyncClient
    ) -> None:
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not.a.jwt"}
        )
        assert response.status_code == 401

    async def test_access_with_valid_token(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/users/me", headers=student_auth)
        assert response.status_code == 200
        assert response.json()["email"] == "student@example.com"
