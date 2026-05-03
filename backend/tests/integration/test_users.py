"""Integration-тесты модуля users: профиль, оценки, пройденные ЦК, нагрузка."""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CKCourse, Discipline

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestGetMe:
    async def test_returns_current_user_fields(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """GET /me возвращает корректные поля текущего пользователя."""
        response = await client.get("/api/v1/users/me", headers=student_auth)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "student@example.com"
        assert data["role"] == "student"
        assert data["is_active"] is True
        assert data["semester"] == 4
        assert data["career_goal"] == "ml"
        assert data["technopark_status"] == "none"
        assert data["workload_pref"] == "normal"
        assert "id" in data
        assert "created_at" in data


class TestProfileUpdate:
    async def test_update_career_goal(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """PATCH /me меняет карьерную цель."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"career_goal": "backend"},
        )
        assert response.status_code == 200
        assert response.json()["career_goal"] == "backend"

        # Проверяем что изменение сохранилось
        check = await client.get("/api/v1/users/me", headers=student_auth)
        assert check.json()["career_goal"] == "backend"

    async def test_update_semester(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """PATCH /me меняет семестр."""
        response = await client.patch(
            "/api/v1/users/me", headers=student_auth, json={"semester": 6}
        )
        assert response.status_code == 200
        assert response.json()["semester"] == 6

    async def test_update_technopark_status(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """PATCH /me меняет статус Технопарка."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"technopark_status": "backend"},
        )
        assert response.status_code == 200
        assert response.json()["technopark_status"] == "backend"

    async def test_update_workload_pref(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """PATCH /me меняет предпочтение по нагрузке."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"workload_pref": "intensive"},
        )
        assert response.status_code == 200
        assert response.json()["workload_pref"] == "intensive"

    async def test_partial_update_does_not_touch_other_fields(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """PATCH одного поля не затирает остальные."""
        # ставим эталонное состояние
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={
                "semester": 5,
                "career_goal": "ml",
                "technopark_status": "ml",
                "workload_pref": "normal",
            },
        )
        # меняем только одно поле
        response = await client.patch(
            "/api/v1/users/me", headers=student_auth, json={"workload_pref": "light"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["workload_pref"] == "light"
        assert data["semester"] == 5
        assert data["career_goal"] == "ml"
        assert data["technopark_status"] == "ml"

    async def test_invalid_semester_zero_returns_422(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Семестр 0 отклоняется валидацией."""
        response = await client.patch(
            "/api/v1/users/me", headers=student_auth, json={"semester": 0}
        )
        assert response.status_code == 422

    async def test_invalid_semester_nine_returns_422(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Семестр 9 отклоняется валидацией."""
        response = await client.patch(
            "/api/v1/users/me", headers=student_auth, json={"semester": 9}
        )
        assert response.status_code == 422

    async def test_invalid_career_goal_returns_422(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Невалидное значение enum отклоняется."""
        response = await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"career_goal": "not_a_real_goal"},
        )
        assert response.status_code == 422


class TestGrades:
    async def test_empty_grades_for_new_user(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """У нового пользователя оценок нет."""
        response = await client.get("/api/v1/users/me/grades", headers=student_auth)
        assert response.status_code == 200
        assert response.json() == []

    async def test_put_grades_then_list(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """PUT сохраняет оценки, GET возвращает их."""
        result = await db.execute(select(Discipline.id).limit(3))
        disc_ids = [str(row[0]) for row in result.all()]
        assert len(disc_ids) == 3

        payload = {
            "grades": [
                {"discipline_id": disc_ids[0], "grade": 5},
                {"discipline_id": disc_ids[1], "grade": 4},
                {"discipline_id": disc_ids[2], "grade": 3},
            ]
        }
        put_response = await client.put(
            "/api/v1/users/me/grades", headers=student_auth, json=payload
        )
        assert put_response.status_code == 200
        assert len(put_response.json()) == 3

        get_response = await client.get(
            "/api/v1/users/me/grades", headers=student_auth
        )
        assert get_response.status_code == 200
        items = get_response.json()
        assert len(items) == 3
        for item in items:
            assert "discipline_id" in item
            assert "discipline_name" in item
            assert 2 <= item["grade"] <= 5

    async def test_put_grades_replaces_existing(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Повторный PUT полностью заменяет старые оценки."""
        result = await db.execute(select(Discipline.id).limit(3))
        disc_ids = [str(row[0]) for row in result.all()]

        # сначала 3 оценки
        await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={
                "grades": [
                    {"discipline_id": disc_ids[0], "grade": 5},
                    {"discipline_id": disc_ids[1], "grade": 4},
                    {"discipline_id": disc_ids[2], "grade": 3},
                ]
            },
        )
        # затем 2 — старые должны исчезнуть
        await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={
                "grades": [
                    {"discipline_id": disc_ids[0], "grade": 5},
                    {"discipline_id": disc_ids[1], "grade": 5},
                ]
            },
        )
        response = await client.get("/api/v1/users/me/grades", headers=student_auth)
        items = response.json()
        assert len(items) == 2
        ids_returned = {item["discipline_id"] for item in items}
        assert disc_ids[2] not in ids_returned

    async def test_put_grade_out_of_range_low_returns_422(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Оценка ниже 2 отклоняется."""
        result = await db.execute(select(Discipline.id).limit(1))
        disc_id = str(result.scalar_one())

        response = await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={"grades": [{"discipline_id": disc_id, "grade": 1}]},
        )
        assert response.status_code == 422

    async def test_put_grade_out_of_range_high_returns_422(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Оценка выше 5 отклоняется."""
        result = await db.execute(select(Discipline.id).limit(1))
        disc_id = str(result.scalar_one())

        response = await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={"grades": [{"discipline_id": disc_id, "grade": 6}]},
        )
        assert response.status_code == 422

    async def test_put_grade_unknown_discipline_returns_404(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Несуществующая дисциплина приводит к 404."""
        response = await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={
                "grades": [
                    {"discipline_id": str(uuid.uuid4()), "grade": 5}
                ]
            },
        )
        assert response.status_code == 404

    async def test_put_empty_grades_clears_all(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Пустой список грейдов очищает все оценки."""
        result = await db.execute(select(Discipline.id).limit(1))
        disc_id = str(result.scalar_one())

        await client.put(
            "/api/v1/users/me/grades",
            headers=student_auth,
            json={"grades": [{"discipline_id": disc_id, "grade": 5}]},
        )
        clear = await client.put(
            "/api/v1/users/me/grades", headers=student_auth, json={"grades": []}
        )
        assert clear.status_code == 200
        assert clear.json() == []


class TestCompletedCK:
    async def test_empty_for_new_user(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """У нового пользователя нет пройденных ЦК."""
        response = await client.get(
            "/api/v1/users/me/completed-ck", headers=student_auth
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_add_existing_ck(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Добавление существующего ЦК возвращает 201 и попадает в список."""
        result = await db.execute(select(CKCourse.id).limit(1))
        ck_id = str(result.scalar_one())

        post = await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": ck_id},
        )
        assert post.status_code == 201
        body = post.json()
        assert body["ck_course_id"] == ck_id
        assert "ck_course_name" in body
        assert "ck_course_category" in body
        assert "completed_at" in body

        listing = await client.get(
            "/api/v1/users/me/completed-ck", headers=student_auth
        )
        assert any(item["ck_course_id"] == ck_id for item in listing.json())

    async def test_add_duplicate_ck_returns_409(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Повторное добавление того же ЦК — 409."""
        result = await db.execute(select(CKCourse.id).limit(1))
        ck_id = str(result.scalar_one())

        first = await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": ck_id},
        )
        assert first.status_code == 201

        dup = await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": ck_id},
        )
        assert dup.status_code == 409

    async def test_add_unknown_ck_returns_404(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Несуществующий ck_course_id — 404."""
        response = await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": str(uuid.uuid4())},
        )
        assert response.status_code == 404

    async def test_delete_completed_ck(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """DELETE убирает ЦК из списка пройденных."""
        result = await db.execute(select(CKCourse.id).limit(1))
        ck_id = str(result.scalar_one())

        await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": ck_id},
        )
        delete = await client.delete(
            f"/api/v1/users/me/completed-ck/{ck_id}", headers=student_auth
        )
        assert delete.status_code == 204

        listing = await client.get(
            "/api/v1/users/me/completed-ck", headers=student_auth
        )
        assert all(item["ck_course_id"] != ck_id for item in listing.json())

    async def test_delete_not_marked_returns_404(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """DELETE для не отмеченного ЦК — 404."""
        result = await db.execute(select(CKCourse.id).limit(1))
        ck_id = str(result.scalar_one())

        response = await client.delete(
            f"/api/v1/users/me/completed-ck/{ck_id}", headers=student_auth
        )
        assert response.status_code == 404


class TestWorkload:
    async def test_workload_structure(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Структура ответа GET /me/workload."""
        response = await client.get("/api/v1/users/me/workload", headers=student_auth)
        assert response.status_code == 200
        data = response.json()
        assert "current_semester" in data
        assert "semesters" in data
        assert "completed_ck_credits" in data
        assert "technopark_credits" in data
        assert "total_extra_credits" in data
        assert isinstance(data["semesters"], list)
        assert len(data["semesters"]) > 0

        for sem in data["semesters"]:
            assert "semester" in sem
            assert "mandatory_credits" in sem
            assert "elective_credits" in sem
            assert "total_curriculum" in sem
            assert (
                sem["mandatory_credits"] + sem["elective_credits"]
                == sem["total_curriculum"]
            )

    async def test_workload_returns_student_semester(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """current_semester соответствует профилю студента."""
        await client.patch(
            "/api/v1/users/me", headers=student_auth, json={"semester": 4}
        )
        response = await client.get("/api/v1/users/me/workload", headers=student_auth)
        assert response.json()["current_semester"] == 4

    async def test_workload_technopark_zero_when_none(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Без участия в ТП — technopark_credits = 0."""
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"technopark_status": "none"},
        )
        response = await client.get("/api/v1/users/me/workload", headers=student_auth)
        data = response.json()
        assert data["technopark_credits"] == 0

    async def test_workload_technopark_six_when_active(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """С участием в ТП — technopark_credits = 6."""
        await client.patch(
            "/api/v1/users/me",
            headers=student_auth,
            json={"technopark_status": "backend"},
        )
        response = await client.get("/api/v1/users/me/workload", headers=student_auth)
        data = response.json()
        assert data["technopark_credits"] == 6
        assert data["total_extra_credits"] == data["completed_ck_credits"] + 6

    async def test_workload_completed_ck_credits_increase(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """После добавления пройденного ЦК completed_ck_credits растёт."""
        before = await client.get("/api/v1/users/me/workload", headers=student_auth)
        before_credits = before.json()["completed_ck_credits"]

        result = await db.execute(select(CKCourse.id, CKCourse.credits).limit(1))
        ck_id, ck_credits = result.first()

        await client.post(
            "/api/v1/users/me/completed-ck",
            headers=student_auth,
            json={"ck_course_id": str(ck_id)},
        )
        after = await client.get("/api/v1/users/me/workload", headers=student_auth)
        assert after.json()["completed_ck_credits"] == before_credits + ck_credits
