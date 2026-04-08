"""Безопасность: хеширование паролей (bcrypt), JWT (PyJWT), refresh-токены."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.config import settings
from app.exceptions import UnauthorizedError


def hash_password(password: str) -> str:
    """Хеширование пароля через bcrypt (12 раундов)."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Проверка пароля. Timing-safe."""
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, role: str) -> str:
    """Создание JWT access-токена."""
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(seconds=settings.jwt_access_token_ttl),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Декодирование и верификация JWT access-токена."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")
    return payload


def create_refresh_token() -> tuple[str, str]:
    """Возвращает (raw_token, sha256_hash). Хэш сохраняется в БД, raw отдаётся клиенту."""
    raw = secrets.token_hex(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def hash_refresh_token(raw: str) -> str:
    """SHA-256 хеш refresh-токена для поиска в БД."""
    return hashlib.sha256(raw.encode()).hexdigest()
