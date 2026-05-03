"""Integration-тесты конструктора правил ЭС: lock + draft/publish + preview + hot-reload."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import async_session_factory
from app.db.models import Rule, UserRole
from app.expert.service import expert_service

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN = "/api/v1/admin"


@pytest_asyncio.fixture(autouse=True, loop_scope="session")
async def _cleanup_test_rules() -> AsyncIterator[None]:
    """После каждого теста — стереть тестовые правила (number >= 1000) и перезагрузить движок.

    Иначе опубликованные правила из предыдущего теста остаются в БД и в памяти движка,
    загрязняя последующие тесты. Production-движок тоже сбрасывается в seed-состояние.
    """
    yield
    async with async_session_factory() as session:
        await session.execute(text("DELETE FROM rules WHERE number >= 1000"))
        await session.commit()
        await expert_service.reload_from_db(session)


# ── Утилиты ───────────────────────────────────────────────────────────────────


async def _next_rule_number(db: AsyncSession) -> int:
    """Вернуть номер правила, не пересекающийся с seed (на 1000 больше максимума)."""
    result = await db.execute(select(Rule.number))
    used = set(result.scalars().all())
    return max(used, default=0) + 1000


def _rule_payload(number: int, **overrides: Any) -> dict[str, Any]:
    """Минимально валидный payload для POST /admin/rules."""
    base: dict[str, Any] = {
        "number": number,
        "group": "ck_programs",
        "name": "Workflow тестовое правило",
        "description": "",
        "condition": {
            "all": [
                {"param": "career_goal", "op": "eq", "value": "qa"},
                {"param": "semester", "op": "gte", "value": 3},
            ]
        },
        "recommendation": {
            "category": "ck_course",
            "title": "WORKFLOW_MARKER: курс по тестированию",
            "priority": "high",
            "reasoning": "тест workflow",
        },
        "priority": 0,
        "is_active": True,
    }
    base.update(overrides)
    return base


# ── 1. Lock: статус, захват, продление, освобождение, force ──────────────────


class TestLock:
    async def test_lock_initially_free(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        response = await client.get(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert response.status_code == 200
        body = response.json()
        assert body["is_locked"] is False
        assert body["admin_id"] is None
        assert body["owned_by_me"] is False

    async def test_acquire_marks_owned_by_me(
        self, client: AsyncClient, admin_auth: dict[str, str], admin
    ) -> None:
        response = await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert response.status_code == 200
        body = response.json()
        assert body["is_locked"] is True
        assert body["owned_by_me"] is True
        assert body["admin_email"] == admin.email
        assert body["expires_at"] is not None

    async def test_repeated_acquire_extends_ttl(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        first = await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        first_expires = first.json()["expires_at"]
        second = await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert second.json()["owned_by_me"] is True
        # TTL продлевается (или равен; поскольку точность секунды, проверяем >=)
        assert second.json()["expires_at"] >= first_expires

    async def test_other_admin_acquire_returns_423(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
        make_user: Any,
    ) -> None:
        # Первый админ занимает лок
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        # Второй админ пытается захватить — отказ 423
        other = await make_user(
            db, email="other-admin@example.com", role=UserRole.ADMIN
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": other.email, "password": "Test12345!"},
        )
        other_auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        response = await client.post(f"{ADMIN}/rules/lock", headers=other_auth)
        assert response.status_code == 423

    async def test_release_frees_lock(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        release = await client.delete(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert release.status_code == 204
        status = await client.get(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert status.json()["is_locked"] is False

    async def test_force_release_takes_others_lock(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
        make_user: Any,
    ) -> None:
        # Первый админ занимает
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        # Второй админ принудительно освобождает
        other = await make_user(
            db, email="force-admin@example.com", role=UserRole.ADMIN
        )
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": other.email, "password": "Test12345!"},
        )
        other_auth = {"Authorization": f"Bearer {login.json()['access_token']}"}
        force = await client.delete(
            f"{ADMIN}/rules/lock/force", headers=other_auth
        )
        assert force.status_code == 204
        status = await client.get(f"{ADMIN}/rules/lock", headers=other_auth)
        assert status.json()["is_locked"] is False
        # Теперь второй админ может захватить
        acquire = await client.post(f"{ADMIN}/rules/lock", headers=other_auth)
        assert acquire.json()["owned_by_me"] is True


# ── 2. Mutating без лока → 423 ───────────────────────────────────────────────


class TestMutationRequiresLock:
    async def test_create_without_lock_returns_423(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        number = await _next_rule_number(db)
        response = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        assert response.status_code == 423

    async def test_patch_without_lock_returns_423(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
    ) -> None:
        # Создаём правило с захваченным локом
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        rule_id = created.json()["id"]
        # Освобождаем
        await client.delete(f"{ADMIN}/rules/lock", headers=admin_auth)
        # PATCH без лока — отказ
        response = await client.patch(
            f"{ADMIN}/rules/{rule_id}",
            headers=admin_auth,
            json={"priority": 99},
        )
        assert response.status_code == 423

    async def test_publish_without_lock_returns_423(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
    ) -> None:
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        rule_id = created.json()["id"]
        await client.delete(f"{ADMIN}/rules/lock", headers=admin_auth)
        response = await client.post(
            f"{ADMIN}/rules/{rule_id}/publish", headers=admin_auth
        )
        assert response.status_code == 423

    async def test_get_lock_status_does_not_require_lock(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        # Read-операции локом не защищены
        response = await client.get(f"{ADMIN}/rules/lock", headers=admin_auth)
        assert response.status_code == 200

    async def test_list_rules_does_not_require_lock(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        response = await client.get(f"{ADMIN}/rules", headers=admin_auth)
        assert response.status_code == 200


# ── 3. Draft → Publish → видимость для студента (hot-reload) ─────────────────


class TestDraftPublishWorkflow:
    async def test_new_rule_is_draft_by_default(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        assert created.status_code == 201
        assert created.json()["is_published"] is False

    async def test_draft_not_visible_to_students(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        # Профиль студента под условие правила: career_goal=qa, semester=5
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"semester": 5, "career_goal": "qa"},
        )
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )

        recs = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        titles = [r["title"] for r in recs.json()]
        assert not any("WORKFLOW_MARKER" in t for t in titles)

    async def test_publish_makes_rule_visible_to_students(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        # Студент с подходящим профилем
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"semester": 5, "career_goal": "qa"},
        )
        # Админ создаёт черновик и публикует
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        rule_id = created.json()["id"]
        publish = await client.post(
            f"{ADMIN}/rules/{rule_id}/publish", headers=admin_auth
        )
        assert publish.status_code == 200
        assert publish.json()["is_published"] is True

        # Hot-reload: новое правило сразу видно студенту, без рестарта
        recs = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        titles = [r["title"] for r in recs.json()]
        assert any("WORKFLOW_MARKER" in t for t in titles), (
            f"Опубликованное правило не появилось в рекомендациях: {titles}"
        )

    async def test_unpublish_removes_rule_from_students(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"semester": 5, "career_goal": "qa"},
        )
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        rule_id = created.json()["id"]
        await client.post(f"{ADMIN}/rules/{rule_id}/publish", headers=admin_auth)

        # Видим до unpublish
        recs_before = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert any(
            "WORKFLOW_MARKER" in r["title"] for r in recs_before.json()
        )

        # Unpublish и проверка отсутствия
        unpublish = await client.post(
            f"{ADMIN}/rules/{rule_id}/unpublish", headers=admin_auth
        )
        assert unpublish.status_code == 200
        assert unpublish.json()["is_published"] is False

        recs_after = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert not any(
            "WORKFLOW_MARKER" in r["title"] for r in recs_after.json()
        )

    async def test_delete_published_rule_removes_from_students(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"semester": 5, "career_goal": "qa"},
        )
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        created = await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )
        rule_id = created.json()["id"]
        await client.post(f"{ADMIN}/rules/{rule_id}/publish", headers=admin_auth)

        delete = await client.delete(
            f"{ADMIN}/rules/{rule_id}", headers=admin_auth
        )
        assert delete.status_code == 204

        recs = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert not any(
            "WORKFLOW_MARKER" in r["title"] for r in recs.json()
        )


# ── 4. Preview: проверка правил до публикации ───────────────────────────────


class TestPreview:
    async def test_preview_includes_drafts_by_default(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )

        profile = {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "semester": 5,
            "career_goal": "qa",
            "technopark_status": "none",
            "workload_pref": "normal",
        }
        response = await client.post(
            f"{ADMIN}/rules/preview",
            headers=admin_auth,
            json={"profile": profile, "include_drafts": True},
        )
        assert response.status_code == 200
        body = response.json()
        titles = [r["title"] for r in body["recommendations"]]
        assert any("WORKFLOW_MARKER" in t for t in titles)
        assert body["total_checked"] >= 1
        assert body["total_fired"] >= 1

    async def test_preview_excludes_drafts_when_flag_off(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )

        profile = {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "semester": 5,
            "career_goal": "qa",
            "technopark_status": "none",
            "workload_pref": "normal",
        }
        response = await client.post(
            f"{ADMIN}/rules/preview",
            headers=admin_auth,
            json={"profile": profile, "include_drafts": False},
        )
        assert response.status_code == 200
        titles = [r["title"] for r in response.json()["recommendations"]]
        assert not any("WORKFLOW_MARKER" in t for t in titles)

    async def test_preview_does_not_affect_production_engine(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,  # noqa: ARG002
    ) -> None:
        # Админ делает preview (с drafts) — production-движок не должен подхватить draft
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"semester": 5, "career_goal": "qa"},
        )
        await client.post(f"{ADMIN}/rules/lock", headers=admin_auth)
        number = await _next_rule_number(db)
        await client.post(
            f"{ADMIN}/rules", headers=admin_auth, json=_rule_payload(number)
        )

        await client.post(
            f"{ADMIN}/rules/preview",
            headers=admin_auth,
            json={
                "profile": {
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "semester": 5,
                    "career_goal": "qa",
                    "technopark_status": "none",
                    "workload_pref": "normal",
                },
                "include_drafts": True,
            },
        )

        # У студента — без изменений
        recs = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert not any(
            "WORKFLOW_MARKER" in r["title"] for r in recs.json()
        )


# ── 5. Авторизация: студент не может работать с конструктором ────────────────


class TestAuthorization:
    async def test_student_cannot_get_lock_status(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.get(f"{ADMIN}/rules/lock", headers=student_auth)
        assert response.status_code == 403

    async def test_student_cannot_acquire_lock(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.post(f"{ADMIN}/rules/lock", headers=student_auth)
        assert response.status_code == 403

    async def test_student_cannot_publish(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        # Дайжем UUID-лайк id, главное проверить 403 до бизнес-логики
        response = await client.post(
            f"{ADMIN}/rules/00000000-0000-0000-0000-000000000000/publish",
            headers=student_auth,
        )
        assert response.status_code == 403

    async def test_student_cannot_preview(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.post(
            f"{ADMIN}/rules/preview",
            headers=student_auth,
            json={
                "profile": {
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "semester": 5,
                    "career_goal": "qa",
                    "technopark_status": "none",
                    "workload_pref": "normal",
                },
                "include_drafts": True,
            },
        )
        assert response.status_code == 403
