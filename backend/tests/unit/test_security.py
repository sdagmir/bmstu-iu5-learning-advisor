from __future__ import annotations

import pytest

from app.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.exceptions import UnauthorizedError


class TestPasswordHashing:
    def test_hash_and_verify(self) -> None:
        password = "secure-password-123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self) -> None:
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_different_hashes_for_same_password(self) -> None:
        password = "same-password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2  # bcrypt каждый раз использует разную соль


class TestAccessToken:
    def test_create_and_decode(self) -> None:
        user_id = "test-user-id-123"
        role = "student"
        token = create_access_token(user_id, role)
        payload = decode_access_token(token)

        assert payload["sub"] == user_id
        assert payload["role"] == role
        assert payload["type"] == "access"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(UnauthorizedError, match="Invalid or expired token"):
            decode_access_token("invalid.token.here")

    def test_tampered_token_raises(self) -> None:
        token = create_access_token("user-id", "student")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(UnauthorizedError):
            decode_access_token(tampered)


class TestRefreshToken:
    def test_create_returns_pair(self) -> None:
        raw, hashed = create_refresh_token()
        assert len(raw) == 64  # две uuid4 hex-строки
        assert len(hashed) == 64  # sha256 hex

    def test_hash_is_deterministic(self) -> None:
        raw, hashed = create_refresh_token()
        assert hash_refresh_token(raw) == hashed

    def test_different_tokens_each_call(self) -> None:
        raw1, _ = create_refresh_token()
        raw2, _ = create_refresh_token()
        assert raw1 != raw2
