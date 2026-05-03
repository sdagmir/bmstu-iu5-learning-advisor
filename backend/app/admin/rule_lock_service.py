"""Сервис pessimistic-лока на редактирование правил ЭС.

Один админ за раз может изменять правила. Лок имеет TTL и автоматически
освобождается при просрочке. Любой админ может принудительно отдать
чужой лок (например, если коллега забыл выйти).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.db.models import RuleEditingLock, User
from app.exceptions import LockedError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# TTL лока. Каждый mutating-запрос продлевает на это значение.
LOCK_TTL = timedelta(minutes=30)
# Singleton primary key — в таблице не более одной записи.
_SLOT = 1


@dataclass(frozen=True)
class LockStatus:
    """Снимок текущего состояния лока для возврата клиенту."""

    is_locked: bool
    admin_id: uuid.UUID | None = None
    admin_email: str | None = None
    acquired_at: datetime | None = None
    expires_at: datetime | None = None
    owned_by_me: bool = False


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _fetch_active(db: AsyncSession) -> RuleEditingLock | None:
    """Текущий лок, если он не просрочен. Просроченный считается отсутствующим."""
    result = await db.execute(select(RuleEditingLock).where(RuleEditingLock.slot == _SLOT))
    lock = result.scalar_one_or_none()
    if lock is None:
        return None
    if lock.expires_at <= _now():
        return None
    return lock


async def get_status(db: AsyncSession, current_admin_id: uuid.UUID) -> LockStatus:
    """Текущее состояние лока для UI: занят/свободен, кем, до какого времени."""
    lock = await _fetch_active(db)
    if lock is None:
        return LockStatus(is_locked=False)
    owner = await db.get(User, lock.admin_id)
    return LockStatus(
        is_locked=True,
        admin_id=lock.admin_id,
        admin_email=owner.email if owner else None,
        acquired_at=lock.acquired_at,
        expires_at=lock.expires_at,
        owned_by_me=lock.admin_id == current_admin_id,
    )


async def acquire(db: AsyncSession, admin_id: uuid.UUID) -> RuleEditingLock:
    """Захватить лок (или продлить, если уже принадлежит этому админу).

    Поднимает LockedError, если лок принадлежит другому админу и ещё не истёк.
    """
    expires = _now() + LOCK_TTL
    existing = await db.execute(select(RuleEditingLock).where(RuleEditingLock.slot == _SLOT))
    lock = existing.scalar_one_or_none()

    if lock is None:
        lock = RuleEditingLock(slot=_SLOT, admin_id=admin_id, expires_at=expires)
        db.add(lock)
        await db.flush()
        return lock

    # Просроченный лок — забираем себе
    if lock.expires_at <= _now():
        lock.admin_id = admin_id
        lock.acquired_at = _now()
        lock.expires_at = expires
        await db.flush()
        return lock

    # Активный лок чужого админа — отказ
    if lock.admin_id != admin_id:
        owner = await db.get(User, lock.admin_id)
        owner_label = owner.email if owner else str(lock.admin_id)
        raise LockedError(
            f"Конструктор правил занят: {owner_label} до {lock.expires_at.isoformat()}"
        )

    # Свой лок — продлеваем TTL
    lock.expires_at = expires
    await db.flush()
    return lock


async def release(db: AsyncSession, admin_id: uuid.UUID) -> bool:
    """Освободить свой лок. Возвращает True, если что-то удалено."""
    lock = await _fetch_active(db)
    if lock is None or lock.admin_id != admin_id:
        return False
    await db.delete(lock)
    await db.flush()
    return True


async def force_release(db: AsyncSession) -> bool:
    """Принудительно освободить лок (например, забытый коллегой)."""
    result = await db.execute(select(RuleEditingLock).where(RuleEditingLock.slot == _SLOT))
    lock = result.scalar_one_or_none()
    if lock is None:
        return False
    await db.delete(lock)
    await db.flush()
    return True


async def assert_owned_by(db: AsyncSession, admin_id: uuid.UUID) -> None:
    """Проверить, что mutating-операцию выполняет владелец активного лока.

    Если лок не захвачен или принадлежит другому — LockedError.
    """
    lock = await _fetch_active(db)
    if lock is None:
        raise LockedError(
            "Сначала захватите лок: POST /api/v1/admin/rules/lock"
        )
    if lock.admin_id != admin_id:
        owner = await db.get(User, lock.admin_id)
        owner_label = owner.email if owner else str(lock.admin_id)
        raise LockedError(
            f"Конструктор правил занят другим админом: {owner_label}"
        )
