"""Integration-тесты модуля admin: CRUD всех 7 сущностей.

Проверяется:
- авторизация (студент → 403 на admin-эндпоинтах);
- управление пользователями (list/get/patch);
- CRUD компетенций, дисциплин, курсов ЦК, направлений, фокусов, правил;
- валидация Pydantic-схем (422) и доменные ошибки (404).

Используются фикстуры из conftest: client, db, student/admin, *_auth, seeded.
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    CareerDirection,
    CKCourse,
    Competency,
    Discipline,
    Rule,
    UserRole,
)

pytestmark = pytest.mark.asyncio(loop_scope="session")

ADMIN_PREFIX = "/api/v1/admin"


# ── Сквозные проверки авторизации ────────────────────────────────────────────


class TestAdminAuthorization:
    """Студент без роли admin должен получать 403 на любом admin-эндпоинте."""

    async def test_student_forbidden_on_users(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.get(f"{ADMIN_PREFIX}/users", headers=student_auth)
        assert response.status_code == 403

    async def test_student_forbidden_on_competencies(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.get(f"{ADMIN_PREFIX}/competencies", headers=student_auth)
        assert response.status_code == 403

    async def test_student_forbidden_on_post_competency(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        response = await client.post(
            f"{ADMIN_PREFIX}/competencies",
            headers=student_auth,
            json={"tag": "X", "name": "test", "category": "math"},
        )
        assert response.status_code == 403

    async def test_anonymous_unauthorized(self, client: AsyncClient) -> None:
        response = await client.get(f"{ADMIN_PREFIX}/users")
        assert response.status_code == 401


# ── Управление пользователями ───────────────────────────────────────────────


class TestUsersAdmin:
    """Эндпоинты /admin/users — список, чтение, обновление."""

    async def test_list_users_returns_200(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student,  # noqa: ARG002 — гарантируем наличие 2+ юзеров
        admin,  # noqa: ARG002
    ) -> None:
        response = await client.get(f"{ADMIN_PREFIX}/users", headers=admin_auth)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        emails = {u["email"] for u in data}
        assert "student@example.com" in emails
        assert "admin@example.com" in emails

    async def test_list_users_pagination(
        self, client: AsyncClient, admin_auth: dict[str, str], student, admin  # noqa: ARG002
    ) -> None:
        # limit=1 — ровно один элемент в выдаче
        response = await client.get(
            f"{ADMIN_PREFIX}/users?offset=0&limit=1", headers=admin_auth
        )
        assert response.status_code == 200
        assert len(response.json()) == 1

        # offset=1 — другой элемент
        response2 = await client.get(
            f"{ADMIN_PREFIX}/users?offset=1&limit=1", headers=admin_auth
        )
        assert response2.status_code == 200
        assert len(response2.json()) == 1
        assert response.json()[0]["id"] != response2.json()[0]["id"]

    async def test_get_user_by_id(
        self, client: AsyncClient, admin_auth: dict[str, str], student
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/users/{student.id}", headers=admin_auth
        )
        assert response.status_code == 200
        assert response.json()["email"] == student.email

    async def test_get_user_unknown_returns_404(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/users/{uuid.uuid4()}", headers=admin_auth
        )
        assert response.status_code == 404

    async def test_patch_user_role_and_active(
        self, client: AsyncClient, admin_auth: dict[str, str], student
    ) -> None:
        # повышаем студента до admin и деактивируем
        response = await client.patch(
            f"{ADMIN_PREFIX}/users/{student.id}",
            headers=admin_auth,
            json={"role": "admin", "is_active": False},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["role"] == "admin"
        assert body["is_active"] is False

        # повторное чтение подтверждает изменения
        again = await client.get(
            f"{ADMIN_PREFIX}/users/{student.id}", headers=admin_auth
        )
        assert again.json()["role"] == "admin"
        assert again.json()["is_active"] is False

        # вернуть обратно
        await client.patch(
            f"{ADMIN_PREFIX}/users/{student.id}",
            headers=admin_auth,
            json={"role": "student", "is_active": True},
        )


# ── Компетенции ──────────────────────────────────────────────────────────────


class TestCompetenciesCRUD:
    """CRUD /admin/competencies."""

    async def test_list_with_seed(
        self, client: AsyncClient, admin_auth: dict[str, str], seeded  # noqa: ARG002
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/competencies?limit=100", headers=admin_auth
        )
        assert response.status_code == 200
        # 38 компетенций seed-данных
        assert len(response.json()) == 38

    async def test_create_competency(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        payload = {
            "tag": f"TST_{uuid.uuid4().hex[:6]}",
            "name": "Тестовая компетенция",
            "category": "programming",
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/competencies", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert body["tag"] == payload["tag"]
        assert body["name"] == payload["name"]
        assert body["category"] == "programming"
        assert "id" in body

    async def test_patch_competency(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        # arrange — создаём, затем меняем
        created = await client.post(
            f"{ADMIN_PREFIX}/competencies",
            headers=admin_auth,
            json={
                "tag": f"PAT_{uuid.uuid4().hex[:6]}",
                "name": "Старое имя",
                "category": "math",
            },
        )
        comp_id = created.json()["id"]

        response = await client.patch(
            f"{ADMIN_PREFIX}/competencies/{comp_id}",
            headers=admin_auth,
            json={"name": "Новое имя", "category": "data"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Новое имя"
        assert response.json()["category"] == "data"

        # повторное чтение через list (single-get эндпоинта нет)
        listed = await client.get(
            f"{ADMIN_PREFIX}/competencies?limit=100", headers=admin_auth
        )
        found = next(c for c in listed.json() if c["id"] == comp_id)
        assert found["name"] == "Новое имя"

    async def test_delete_competency(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        db: AsyncSession,
    ) -> None:
        created = await client.post(
            f"{ADMIN_PREFIX}/competencies",
            headers=admin_auth,
            json={
                "tag": f"DEL_{uuid.uuid4().hex[:6]}",
                "name": "На удаление",
                "category": "ml",
            },
        )
        comp_id = created.json()["id"]

        delete = await client.delete(
            f"{ADMIN_PREFIX}/competencies/{comp_id}", headers=admin_auth
        )
        assert delete.status_code == 204

        # Прямая проверка по БД — записи нет
        result = await db.execute(
            select(Competency).where(Competency.id == uuid.UUID(comp_id))
        )
        assert result.scalar_one_or_none() is None

        # Повторное удаление → 404
        delete_again = await client.delete(
            f"{ADMIN_PREFIX}/competencies/{comp_id}", headers=admin_auth
        )
        assert delete_again.status_code == 404

    async def test_duplicate_tag_rejected(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        tag = f"DUP_{uuid.uuid4().hex[:6]}"
        first = await client.post(
            f"{ADMIN_PREFIX}/competencies",
            headers=admin_auth,
            json={"tag": tag, "name": "Первая", "category": "programming"},
        )
        assert first.status_code == 201

        second = await client.post(
            f"{ADMIN_PREFIX}/competencies",
            headers=admin_auth,
            json={"tag": tag, "name": "Вторая", "category": "math"},
        )
        # Уникальность tag нарушена — ожидаем ошибку (4xx или 5xx без отдельного хендлера)
        assert second.status_code >= 400


# ── Дисциплины ──────────────────────────────────────────────────────────────


class TestDisciplinesCRUD:
    """CRUD /admin/disciplines."""

    async def test_list_with_seed(
        self, client: AsyncClient, admin_auth: dict[str, str], seeded  # noqa: ARG002
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/disciplines?limit=100", headers=admin_auth
        )
        assert response.status_code == 200
        assert len(response.json()) == 64

    async def test_create_with_empty_competencies(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        payload = {
            "name": "Тестовая дисциплина",
            "semester": 3,
            "credits": 4,
            "type": "mandatory",
            "control_form": "экзамен",
            "competency_ids": [],
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/disciplines", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == payload["name"]
        assert body["semester"] == 3
        assert body["competencies"] == []

    async def test_create_with_competencies(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        # Берём 2 реальные компетенции из seed
        result = await db.execute(select(Competency).limit(2))
        comps = list(result.scalars().all())
        assert len(comps) == 2

        payload = {
            "name": "Дисциплина с компетенциями",
            "semester": 5,
            "credits": 3,
            "type": "elective",
            "control_form": "зачёт",
            "competency_ids": [str(c.id) for c in comps],
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/disciplines", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert len(body["competencies"]) == 2
        returned_ids = {c["id"] for c in body["competencies"]}
        assert returned_ids == {str(c.id) for c in comps}

    async def test_patch_replaces_competencies(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        result = await db.execute(select(Competency).limit(3))
        comps = list(result.scalars().all())
        assert len(comps) == 3

        # Создаём с первыми двумя
        created = await client.post(
            f"{ADMIN_PREFIX}/disciplines",
            headers=admin_auth,
            json={
                "name": "Patch-тест",
                "semester": 2,
                "credits": 2,
                "type": "mandatory",
                "control_form": "зачёт",
                "competency_ids": [str(comps[0].id), str(comps[1].id)],
            },
        )
        assert created.status_code == 201
        disc_id = created.json()["id"]

        # PATCH — заменяем на третью (по правилу проекта: PATCH заменяет, не дополняет)
        patched = await client.patch(
            f"{ADMIN_PREFIX}/disciplines/{disc_id}",
            headers=admin_auth,
            json={"competency_ids": [str(comps[2].id)]},
        )
        assert patched.status_code == 200
        assert len(patched.json()["competencies"]) == 1
        assert patched.json()["competencies"][0]["id"] == str(comps[2].id)

    async def test_delete_discipline(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        created = await client.post(
            f"{ADMIN_PREFIX}/disciplines",
            headers=admin_auth,
            json={
                "name": "Под удаление",
                "semester": 1,
                "credits": 2,
                "type": "mandatory",
                "control_form": "зачёт",
                "competency_ids": [],
            },
        )
        disc_id = created.json()["id"]

        response = await client.delete(
            f"{ADMIN_PREFIX}/disciplines/{disc_id}", headers=admin_auth
        )
        assert response.status_code == 204

        result = await db.execute(
            select(Discipline).where(Discipline.id == uuid.UUID(disc_id))
        )
        assert result.scalar_one_or_none() is None

    async def test_invalid_semester_returns_422(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        base_payload = {
            "name": "Bad",
            "credits": 2,
            "type": "mandatory",
            "control_form": "зачёт",
            "competency_ids": [],
        }
        # semester=0 — ниже допустимого ge=1
        response_low = await client.post(
            f"{ADMIN_PREFIX}/disciplines",
            headers=admin_auth,
            json={**base_payload, "semester": 0},
        )
        assert response_low.status_code == 422

        # semester=9 — выше le=8
        response_high = await client.post(
            f"{ADMIN_PREFIX}/disciplines",
            headers=admin_auth,
            json={**base_payload, "semester": 9},
        )
        assert response_high.status_code == 422


# ── Программы ЦК ────────────────────────────────────────────────────────────


class TestCKCoursesCRUD:
    """CRUD /admin/ck-courses."""

    async def test_list_with_seed(
        self, client: AsyncClient, admin_auth: dict[str, str], seeded  # noqa: ARG002
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/ck-courses?limit=100", headers=admin_auth
        )
        assert response.status_code == 200
        assert len(response.json()) == 20

    async def test_create_with_competencies_and_prereqs(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        result = await db.execute(select(Competency).limit(3))
        comps = list(result.scalars().all())
        assert len(comps) == 3

        payload = {
            "name": f"Тестовый курс ЦК {uuid.uuid4().hex[:6]}",
            "description": "Описание",
            "category": "ml",
            "credits": 3,
            "competency_ids": [str(comps[0].id), str(comps[1].id)],
            "prerequisite_ids": [str(comps[2].id)],
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/ck-courses", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert len(body["competencies"]) == 2
        assert len(body["prerequisites"]) == 1
        assert body["prerequisites"][0]["id"] == str(comps[2].id)

    async def test_patch_replaces_prerequisites(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        result = await db.execute(select(Competency).limit(3))
        comps = list(result.scalars().all())

        created = await client.post(
            f"{ADMIN_PREFIX}/ck-courses",
            headers=admin_auth,
            json={
                "name": f"Курс для PATCH {uuid.uuid4().hex[:6]}",
                "category": "development",
                "credits": 2,
                "competency_ids": [],
                "prerequisite_ids": [str(comps[0].id), str(comps[1].id)],
            },
        )
        course_id = created.json()["id"]

        patched = await client.patch(
            f"{ADMIN_PREFIX}/ck-courses/{course_id}",
            headers=admin_auth,
            json={"prerequisite_ids": [str(comps[2].id)]},
        )
        assert patched.status_code == 200
        # Замена, не дополнение
        assert len(patched.json()["prerequisites"]) == 1
        assert patched.json()["prerequisites"][0]["id"] == str(comps[2].id)

    async def test_delete_ck_course(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        created = await client.post(
            f"{ADMIN_PREFIX}/ck-courses",
            headers=admin_auth,
            json={
                "name": f"Удалить-курс {uuid.uuid4().hex[:6]}",
                "category": "other",
                "credits": 2,
                "competency_ids": [],
                "prerequisite_ids": [],
            },
        )
        course_id = created.json()["id"]

        response = await client.delete(
            f"{ADMIN_PREFIX}/ck-courses/{course_id}", headers=admin_auth
        )
        assert response.status_code == 204

        result = await db.execute(
            select(CKCourse).where(CKCourse.id == uuid.UUID(course_id))
        )
        assert result.scalar_one_or_none() is None

    async def test_duplicate_name_rejected(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        name = f"Уник-курс {uuid.uuid4().hex[:6]}"
        first = await client.post(
            f"{ADMIN_PREFIX}/ck-courses",
            headers=admin_auth,
            json={
                "name": name,
                "category": "ml",
                "credits": 2,
                "competency_ids": [],
                "prerequisite_ids": [],
            },
        )
        assert first.status_code == 201

        second = await client.post(
            f"{ADMIN_PREFIX}/ck-courses",
            headers=admin_auth,
            json={
                "name": name,
                "category": "development",
                "credits": 2,
                "competency_ids": [],
                "prerequisite_ids": [],
            },
        )
        # Имя уникально — повтор должен отклоняться (ожидаем 409 или 4xx/5xx)
        assert second.status_code >= 400


# ── Карьерные направления ───────────────────────────────────────────────────


class TestCareerDirectionsCRUD:
    """CRUD /admin/career-directions."""

    async def test_list_with_seed(
        self, client: AsyncClient, admin_auth: dict[str, str], seeded  # noqa: ARG002
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/career-directions?limit=100", headers=admin_auth
        )
        assert response.status_code == 200
        assert len(response.json()) == 10

    async def test_create_with_competencies(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        result = await db.execute(select(Competency).limit(2))
        comps = list(result.scalars().all())

        payload = {
            "name": f"Тестовое направление {uuid.uuid4().hex[:6]}",
            "description": "Описание направления",
            "example_jobs": "Junior, Middle",
            "competency_ids": [str(c.id) for c in comps],
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/career-directions", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == payload["name"]
        assert len(body["competencies"]) == 2

    async def test_patch_career_direction(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        created = await client.post(
            f"{ADMIN_PREFIX}/career-directions",
            headers=admin_auth,
            json={
                "name": f"PATCH-направление {uuid.uuid4().hex[:6]}",
                "description": "До",
                "example_jobs": None,
                "competency_ids": [],
            },
        )
        direction_id = created.json()["id"]

        patched = await client.patch(
            f"{ADMIN_PREFIX}/career-directions/{direction_id}",
            headers=admin_auth,
            json={"description": "После", "example_jobs": "Senior"},
        )
        assert patched.status_code == 200
        assert patched.json()["description"] == "После"
        assert patched.json()["example_jobs"] == "Senior"

    async def test_delete_career_direction(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        created = await client.post(
            f"{ADMIN_PREFIX}/career-directions",
            headers=admin_auth,
            json={
                "name": f"DEL-направление {uuid.uuid4().hex[:6]}",
                "description": None,
                "example_jobs": None,
                "competency_ids": [],
            },
        )
        direction_id = created.json()["id"]

        response = await client.delete(
            f"{ADMIN_PREFIX}/career-directions/{direction_id}", headers=admin_auth
        )
        assert response.status_code == 204

        result = await db.execute(
            select(CareerDirection).where(CareerDirection.id == uuid.UUID(direction_id))
        )
        assert result.scalar_one_or_none() is None


# ── Таблица фокусов ─────────────────────────────────────────────────────────


class TestFocusAdvicesCRUD:
    """CRUD /admin/focus-advices."""

    async def test_list_focus_advices(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/focus-advices", headers=admin_auth
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_create_focus_advice(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        disc = (await db.execute(select(Discipline).limit(1))).scalar_one()
        direction = (await db.execute(select(CareerDirection).limit(1))).scalar_one()

        payload = {
            "discipline_id": str(disc.id),
            "career_direction_id": str(direction.id),
            "focus_advice": "Сфокусируйся на градиентном бустинге",
            "reasoning": "Часто встречается в ML-вакансиях",
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/focus-advices", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert body["discipline_id"] == str(disc.id)
        assert body["career_direction_id"] == str(direction.id)
        assert body["focus_advice"] == payload["focus_advice"]

    async def test_duplicate_focus_pair_rejected(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        # Берём другую пару, отличающуюся от созданной выше
        discs = (await db.execute(select(Discipline).limit(2))).scalars().all()
        directions = (
            await db.execute(select(CareerDirection).limit(2))
        ).scalars().all()
        disc = discs[1]
        direction = directions[1]

        payload = {
            "discipline_id": str(disc.id),
            "career_direction_id": str(direction.id),
            "focus_advice": "Первый совет",
        }
        first = await client.post(
            f"{ADMIN_PREFIX}/focus-advices", headers=admin_auth, json=payload
        )
        assert first.status_code == 201

        second = await client.post(
            f"{ADMIN_PREFIX}/focus-advices",
            headers=admin_auth,
            json={**payload, "focus_advice": "Второй совет"},
        )
        # uq_focus_disc_career — нарушение уникальности
        assert second.status_code >= 400

    async def test_delete_focus_advice(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded,  # noqa: ARG002
        db: AsyncSession,
    ) -> None:
        # Используем третью пару, чтобы не пересечься с предыдущими тестами
        discs = (await db.execute(select(Discipline).limit(3))).scalars().all()
        directions = (
            await db.execute(select(CareerDirection).limit(3))
        ).scalars().all()
        disc = discs[2]
        direction = directions[2]

        created = await client.post(
            f"{ADMIN_PREFIX}/focus-advices",
            headers=admin_auth,
            json={
                "discipline_id": str(disc.id),
                "career_direction_id": str(direction.id),
                "focus_advice": "На удаление",
            },
        )
        assert created.status_code == 201
        advice_id = created.json()["id"]

        response = await client.delete(
            f"{ADMIN_PREFIX}/focus-advices/{advice_id}", headers=admin_auth
        )
        assert response.status_code == 204


# ── Правила ЭС ──────────────────────────────────────────────────────────────


class TestRulesCRUD:
    """CRUD /admin/rules."""

    async def test_list_with_seed(
        self, client: AsyncClient, admin_auth: dict[str, str], seeded  # noqa: ARG002
    ) -> None:
        response = await client.get(
            f"{ADMIN_PREFIX}/rules?limit=100", headers=admin_auth
        )
        assert response.status_code == 200
        # Минимум — около 50 правил из seed; точное число зависит от rules_data
        assert len(response.json()) >= 1

    async def test_create_rule(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        # Mutating правил требует захваченный лок (фича конструктора)
        lock = await client.post(f"{ADMIN_PREFIX}/rules/lock", headers=admin_auth)
        assert lock.status_code == 200
        # Подбираем уникальный номер правила, чтобы не конфликтовать с seed
        result = await db.execute(select(Rule.number))
        used = {row for row in result.scalars().all()}
        number = max(used, default=0) + 1000

        payload = {
            "number": number,
            "group": "ck_programs",
            "name": "Тестовое правило",
            "description": "Описание",
            "condition": {"career_goal": "ml", "semester": {"$gte": 4}},
            "recommendation": {
                "category": "ck_course",
                "course": "Введение в ML",
                "priority": "high",
            },
            "priority": 5,
            "is_active": True,
        }
        response = await client.post(
            f"{ADMIN_PREFIX}/rules", headers=admin_auth, json=payload
        )
        assert response.status_code == 201
        body = response.json()
        assert body["number"] == number
        assert body["group"] == "ck_programs"
        assert body["condition"] == payload["condition"]
        assert body["recommendation"] == payload["recommendation"]

    async def test_patch_rule_priority_and_active(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        await client.post(f"{ADMIN_PREFIX}/rules/lock", headers=admin_auth)
        result = await db.execute(select(Rule.number))
        used = {row for row in result.scalars().all()}
        number = max(used, default=0) + 1000

        created = await client.post(
            f"{ADMIN_PREFIX}/rules",
            headers=admin_auth,
            json={
                "number": number,
                "group": "warnings",
                "name": "Правило для PATCH",
                "condition": {"x": 1},
                "recommendation": {"category": "warning", "message": "warn"},
                "priority": 0,
                "is_active": True,
            },
        )
        rule_id = created.json()["id"]

        patched = await client.patch(
            f"{ADMIN_PREFIX}/rules/{rule_id}",
            headers=admin_auth,
            json={"priority": 99, "is_active": False},
        )
        assert patched.status_code == 200
        assert patched.json()["priority"] == 99
        assert patched.json()["is_active"] is False

    async def test_delete_rule(
        self, client: AsyncClient, admin_auth: dict[str, str], db: AsyncSession
    ) -> None:
        await client.post(f"{ADMIN_PREFIX}/rules/lock", headers=admin_auth)
        result = await db.execute(select(Rule.number))
        used = {row for row in result.scalars().all()}
        number = max(used, default=0) + 1000

        created = await client.post(
            f"{ADMIN_PREFIX}/rules",
            headers=admin_auth,
            json={
                "number": number,
                "group": "strategy",
                "name": "Удаляемое правило",
                "condition": {},
                "recommendation": {"category": "strategy", "text": "x"},
            },
        )
        rule_id = created.json()["id"]

        response = await client.delete(
            f"{ADMIN_PREFIX}/rules/{rule_id}", headers=admin_auth
        )
        assert response.status_code == 204

        # 404 при повторном удалении
        again = await client.delete(
            f"{ADMIN_PREFIX}/rules/{rule_id}", headers=admin_auth
        )
        assert again.status_code == 404


# ── Проверка ролей через make_user ──────────────────────────────────────────


class TestPatchUserRoleRoundTrip:
    """Дополнительная проверка PATCH с use_user — изолированно от admin/student."""

    async def test_promote_and_demote_user(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        make_user,
        db: AsyncSession,
    ) -> None:
        user = await make_user(db, email=f"extra-{uuid.uuid4().hex[:6]}@example.com")
        assert user.role == UserRole.STUDENT

        # promote
        promote = await client.patch(
            f"{ADMIN_PREFIX}/users/{user.id}",
            headers=admin_auth,
            json={"role": "admin"},
        )
        assert promote.status_code == 200
        assert promote.json()["role"] == "admin"

        # demote обратно
        demote = await client.patch(
            f"{ADMIN_PREFIX}/users/{user.id}",
            headers=admin_auth,
            json={"role": "student"},
        )
        assert demote.status_code == 200
        assert demote.json()["role"] == "student"
