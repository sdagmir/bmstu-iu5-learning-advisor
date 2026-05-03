"""End-to-end сценарные тесты бэкенда РС ИТО.

E2E здесь — последовательность HTTP-запросов через `client`, имитирующая полный
путь пользователя через несколько эндпоинтов разных модулей: auth → users →
catalog → expert → chat → rag → admin.

Каждый тест-метод реализует один сценарий и потому намеренно длинный.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CKCourse, Discipline, User, UserRole
from app.expert.service import expert_service
from tests.integration._fakes import FakeEmbeddingClient, FakeLLMClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ── Хелперы ───────────────────────────────────────────────────────────────────


async def _register(
    client: AsyncClient, email: str, password: str = "StrongPass1!"
) -> dict[str, Any]:
    """Зарегистрировать студента через API и вернуть Authorization-заголовок + токены."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


# ── Сценарий 1: полный путь нового студента ──────────────────────────────────


class TestStudentJourney:
    """Студент проходит весь happy-path: регистрация → профиль → каталоги → рекомендации."""

    async def test_full_new_student_path(
        self,
        client: AsyncClient,
        seeded: None,
        db: AsyncSession,
    ) -> None:
        """Новый студент регистрируется, заполняет профиль и получает рекомендации."""
        # 1. Регистрация
        auth = await _register(client, "journey@example.com")
        headers = auth["headers"]

        # 2. Дефолтный профиль — без semester и career_goal
        me = await client.get("/api/v1/users/me", headers=headers)
        assert me.status_code == 200
        me_data = me.json()
        assert me_data["email"] == "journey@example.com"
        assert me_data["role"] == "student"
        assert me_data["is_active"] is True
        assert me_data["semester"] is None
        assert me_data["career_goal"] is None

        # 3. Заполнение профиля X1-X4
        patch = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={
                "semester": 4,
                "career_goal": "ml",
                "workload_pref": "normal",
            },
        )
        assert patch.status_code == 200
        patched = patch.json()
        assert patched["semester"] == 4
        assert patched["career_goal"] == "ml"
        assert patched["workload_pref"] == "normal"

        # 4. Каталог пройденных дисциплин (1-4 семестры)
        cat_disc = await client.get(
            "/api/v1/catalog/disciplines?semester_max=4", headers=headers
        )
        assert cat_disc.status_code == 200
        disciplines = cat_disc.json()
        assert isinstance(disciplines, list)
        assert len(disciplines) > 0
        assert all(d["semester"] <= 4 for d in disciplines)

        # 5. Отправка оценок по 3 дисциплинам
        result = await db.execute(select(Discipline.id).limit(3))
        disc_ids = [str(row[0]) for row in result.all()]
        assert len(disc_ids) == 3

        put_grades = await client.put(
            "/api/v1/users/me/grades",
            headers=headers,
            json={
                "grades": [
                    {"discipline_id": disc_ids[0], "grade": 5},
                    {"discipline_id": disc_ids[1], "grade": 4},
                    {"discipline_id": disc_ids[2], "grade": 3},
                ]
            },
        )
        assert put_grades.status_code == 200
        assert len(put_grades.json()) == 3

        # 6. Каталог ЦК
        cat_ck = await client.get("/api/v1/catalog/ck-courses", headers=headers)
        assert cat_ck.status_code == 200
        ck_courses = cat_ck.json()
        assert len(ck_courses) > 0

        # 7. Отметить один ЦК как пройденный
        ck_id = ck_courses[0]["id"]
        post_ck = await client.post(
            "/api/v1/users/me/completed-ck",
            headers=headers,
            json={"ck_course_id": ck_id},
        )
        assert post_ck.status_code == 201
        assert post_ck.json()["ck_course_id"] == ck_id

        # 8. Нагрузка
        workload = await client.get("/api/v1/users/me/workload", headers=headers)
        assert workload.status_code == 200
        wdata = workload.json()
        assert wdata["current_semester"] == 4
        assert wdata["completed_ck_credits"] >= 1
        assert isinstance(wdata["semesters"], list)

        # 9. Персональные рекомендации
        recs = await client.get("/api/v1/expert/my-recommendations", headers=headers)
        assert recs.status_code == 200
        recs_data = recs.json()
        assert isinstance(recs_data, list)
        # ML-цель + slabое программирование: должны быть рекомендации
        assert len(recs_data) > 0
        for rec in recs_data:
            assert "rule_id" in rec
            assert "category" in rec
            assert "title" in rec
            assert "priority" in rec
            assert "reasoning" in rec


# ── Сценарий 2: refresh-флоу ─────────────────────────────────────────────────


class TestRefreshLifecycle:
    """Долгий сеанс: refresh ротирует токены, повтор и logout инвалидируют."""

    async def test_refresh_rotation_and_logout(self, client: AsyncClient) -> None:
        """T1.refresh → T2 → повторный T1.refresh даёт 401, logout по T2."""
        t1 = await _register(client, "refresh@example.com")

        # T1.refresh → T2
        r2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": t1["refresh_token"]},
        )
        assert r2.status_code == 200
        t2 = r2.json()
        assert t2["refresh_token"] != t1["refresh_token"]

        # Повторный refresh старым T1 — 401 (он отозван)
        replay = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": t1["refresh_token"]},
        )
        assert replay.status_code == 401

        # Logout по T2
        logout = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": t2["refresh_token"]},
        )
        assert logout.status_code == 204

        # Refresh по T2 после logout — 401
        after_logout = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": t2["refresh_token"]},
        )
        assert after_logout.status_code == 401


# ── Сценарии 3, 4: чат-бот ────────────────────────────────────────────────────


class TestChatFlow:
    """Студент общается с чат-ботом, LLM вызывает ЭС через function calling."""

    async def test_chat_get_recommendations(
        self,
        client: AsyncClient,
        seeded: None,
        fake_llm: FakeLLMClient,
    ) -> None:
        """Сценарий 3: студент спрашивает совет, LLM вызывает get_recommendations и отвечает."""
        auth = await _register(client, "chat1@example.com")
        headers = auth["headers"]

        # Заполняем профиль
        patch = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"semester": 4, "career_goal": "ml"},
        )
        assert patch.status_code == 200

        # 1-й вызов LLM → tool call get_recommendations
        # 2-й вызов LLM → финальный текст
        fake_llm.queue_tool_call("get_recommendations", "{}")
        fake_llm.queue_text("вот рекомендации: ML-курс «Введение в ML»")

        chat = await client.post(
            "/api/v1/chat/message",
            headers=headers,
            json={"message": "что мне взять?"},
        )
        assert chat.status_code == 200, chat.text
        body = chat.json()
        assert "вот рекомендации" in body["reply"]
        assert "ML-курс" in body["reply"]

        # LLM был вызван минимум 2 раза (tool round + финал)
        assert len(fake_llm.calls) >= 2

        # Во втором вызове должен быть tool-result от get_recommendations
        second_call_messages = fake_llm.calls[1]["messages"]
        roles = [m.get("role") for m in second_call_messages]
        assert "tool" in roles

    async def test_chat_recalculate_does_not_persist(
        self,
        client: AsyncClient,
        seeded: None,
        fake_llm: FakeLLMClient,
        db: AsyncSession,
    ) -> None:
        """Сценарий 4: recalculate_with_changes — what-if, не меняет профиль в БД."""
        auth = await _register(client, "chat2@example.com")
        headers = auth["headers"]

        # Профиль = ML
        await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"semester": 4, "career_goal": "ml"},
        )

        fake_llm.queue_tool_call(
            "recalculate_with_changes", '{"career_goal": "backend"}'
        )
        fake_llm.queue_text("для backend рекомендуем backend-трек Технопарка")

        chat = await client.post(
            "/api/v1/chat/message",
            headers=headers,
            json={"message": "а если backend?"},
        )
        assert chat.status_code == 200
        assert "для backend" in chat.json()["reply"]

        # КЛЮЧЕВАЯ проверка: профиль студента в БД остался ML — what-if не персистится
        me = await client.get("/api/v1/users/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["career_goal"] == "ml"

        # Дополнительно проверим напрямую в БД
        result = await db.execute(
            select(User).where(User.email == "chat2@example.com")
        )
        user_db = result.scalar_one()
        assert user_db.career_goal.value == "ml"


# ── Сценарий 5: админ → студент через правило ────────────────────────────────


class TestAdminToStudentFlow:
    """Админ создаёт правило → студент с подходящим профилем видит результат."""

    async def test_admin_rule_appears_in_student_recommendations(
        self,
        client: AsyncClient,
        db: AsyncSession,
        seeded: None,
        make_user: Any,
    ) -> None:
        """Создание правила админом + reload движка → правило срабатывает у студента."""
        # Сохраняем исходный engine, чтобы вернуть его после теста
        original_engine = expert_service._engine
        # Админ через make_user (для Authorization получаем токен через /auth/login)
        admin_user = await make_user(
            db, email="admin-e2e@example.com", role=UserRole.ADMIN
        )
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "Test12345!"},
        )
        assert admin_login.status_code == 200
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        # Админ создаёт правило с уникальным условием — career_goal = qa
        # (мало seed-правил под qa → проще проверить новое правило)
        rule_payload = {
            "number": 999,
            "group": "ck_programs",
            "name": "E2E: QA → ЦК тестирования",
            "description": "Тестовое правило для e2e",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "qa"},
                    {"param": "semester", "op": "gte", "value": 3},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "E2E_RULE_MARKER: QA-курс по тестированию",
                "priority": "high",
                "reasoning": "Карьерная цель QA, проверка e2e-правила",
                "competency_gap": "qa_basics",
            },
            "priority": 0,
            "is_active": True,
        }
        # Конструктор требует захвата лока
        lock_resp = await client.post(
            "/api/v1/admin/rules/lock", headers=admin_headers
        )
        assert lock_resp.status_code == 200

        post = await client.post(
            "/api/v1/admin/rules", headers=admin_headers, json=rule_payload
        )
        assert post.status_code == 201, post.text
        rule_id = post.json()["id"]

        # Создаём правило → оно draft → публикуем; publish сам триггерит hot-reload
        publish_resp = await client.post(
            f"/api/v1/admin/rules/{rule_id}/publish", headers=admin_headers
        )
        assert publish_resp.status_code == 200, publish_resp.text
        assert publish_resp.json()["is_published"] is True

        # Создаём студента и ставим профиль, под который сработает новое правило
        student_auth_data = await _register(client, "qa-student@example.com")
        s_headers = student_auth_data["headers"]
        patch = await client.patch(
            "/api/v1/users/me",
            headers=s_headers,
            json={"semester": 5, "career_goal": "qa"},
        )
        assert patch.status_code == 200

        # Получаем рекомендации — среди них должна быть наша
        try:
            recs = await client.get(
                "/api/v1/expert/my-recommendations", headers=s_headers
            )
            assert recs.status_code == 200
            titles = [r["title"] for r in recs.json()]
            assert any("E2E_RULE_MARKER" in t for t in titles), (
                f"Новое правило не сработало. Получены: {titles}"
            )
        finally:
            # Возвращаем исходный engine, чтобы не повлиять на другие тесты
            expert_service._engine = original_engine


# ── Сценарий 6: документ из RAG найден через чат ─────────────────────────────


class TestRagToChatFlow:
    """Админ загружает документ → студент через чат получает search_knowledge с результатами."""

    async def test_uploaded_document_reachable_via_chat(
        self,
        client: AsyncClient,
        db: AsyncSession,
        seeded: None,
        make_user: Any,
        fake_llm: FakeLLMClient,
        fake_embedder: FakeEmbeddingClient,
    ) -> None:
        """Админ грузит документ, студент через чат вызывает search_knowledge."""
        # Админ
        admin_user = await make_user(
            db, email="admin-rag@example.com", role=UserRole.ADMIN
        )
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": admin_user.email, "password": "Test12345!"},
        )
        admin_headers = {
            "Authorization": f"Bearer {admin_login.json()['access_token']}"
        }

        # Загрузка документа
        upload = await client.post(
            "/api/v1/rag/documents",
            headers=admin_headers,
            json={
                "source": "ck-ml.txt",
                "text": (
                    "Курс «Инженер ML» учит нейросетям и градиентному спуску. "
                    "Программа рассчитана на студентов 4-6 семестров. "
                    "Длительность — два семестра, итоговый проект."
                ),
            },
        )
        assert upload.status_code == 201, upload.text
        assert upload.json()["chunks_count"] > 0

        # Статистика — chunks > 0
        stats = await client.get("/api/v1/rag/stats", headers=admin_headers)
        assert stats.status_code == 200
        assert stats.json()["total_chunks"] > 0

        # Студент общается через чат, LLM вызывает search_knowledge
        student_auth_data = await _register(client, "rag-student@example.com")
        s_headers = student_auth_data["headers"]
        await client.patch(
            "/api/v1/users/me",
            headers=s_headers,
            json={"semester": 4, "career_goal": "ml"},
        )

        fake_llm.queue_tool_call("search_knowledge", '{"query": "ML"}')
        fake_llm.queue_text("нашёл информацию о курсе «Инженер ML»")

        chat = await client.post(
            "/api/v1/chat/message",
            headers=s_headers,
            json={"message": "расскажи про ML-курс"},
        )
        assert chat.status_code == 200
        assert "Инженер ML" in chat.json()["reply"]

        # Минимум 2 вызова LLM, во втором — tool result
        assert len(fake_llm.calls) >= 2
        tool_messages = [
            m for m in fake_llm.calls[1]["messages"] if m.get("role") == "tool"
        ]
        assert len(tool_messages) >= 1
        # tool result должен содержать упоминание загруженного источника
        tool_content = tool_messages[0].get("content", "")
        assert "ck-ml.txt" in tool_content or "Инженер ML" in tool_content


# ── Сценарий 7: изоляция студентов ───────────────────────────────────────────


class TestStudentIsolation:
    """Профили и рекомендации разных студентов не пересекаются."""

    async def test_two_students_have_independent_state(
        self,
        client: AsyncClient,
        db: AsyncSession,
        seeded: None,
    ) -> None:
        """Студенты A и B заполняют разные профили — данные не смешиваются."""
        auth_a = await _register(client, "iso-a@example.com")
        auth_b = await _register(client, "iso-b@example.com")
        headers_a = auth_a["headers"]
        headers_b = auth_b["headers"]

        # A: семестр 3, ML
        pa = await client.patch(
            "/api/v1/users/me",
            headers=headers_a,
            json={"semester": 3, "career_goal": "ml"},
        )
        assert pa.status_code == 200

        # B: семестр 6, backend
        pb = await client.patch(
            "/api/v1/users/me",
            headers=headers_b,
            json={"semester": 6, "career_goal": "backend"},
        )
        assert pb.status_code == 200

        # Оценки — три первые дисциплины, разные баллы
        result = await db.execute(select(Discipline.id).limit(3))
        disc_ids = [str(row[0]) for row in result.all()]

        await client.put(
            "/api/v1/users/me/grades",
            headers=headers_a,
            json={
                "grades": [
                    {"discipline_id": disc_ids[0], "grade": 5},
                    {"discipline_id": disc_ids[1], "grade": 5},
                ]
            },
        )
        await client.put(
            "/api/v1/users/me/grades",
            headers=headers_b,
            json={
                "grades": [
                    {"discipline_id": disc_ids[0], "grade": 3},
                    {"discipline_id": disc_ids[1], "grade": 3},
                    {"discipline_id": disc_ids[2], "grade": 3},
                ]
            },
        )

        # Профили различаются
        me_a = await client.get("/api/v1/users/me", headers=headers_a)
        me_b = await client.get("/api/v1/users/me", headers=headers_b)
        assert me_a.json()["semester"] == 3
        assert me_a.json()["career_goal"] == "ml"
        assert me_b.json()["semester"] == 6
        assert me_b.json()["career_goal"] == "backend"
        assert me_a.json()["id"] != me_b.json()["id"]

        # Оценки изолированы
        grades_a = await client.get("/api/v1/users/me/grades", headers=headers_a)
        grades_b = await client.get("/api/v1/users/me/grades", headers=headers_b)
        assert len(grades_a.json()) == 2
        assert len(grades_b.json()) == 3

        # Пройденные ЦК — разные ЦК для A и B
        ck_result = await db.execute(select(CKCourse.id).limit(2))
        ck_ids = [str(row[0]) for row in ck_result.all()]
        assert len(ck_ids) == 2

        await client.post(
            "/api/v1/users/me/completed-ck",
            headers=headers_a,
            json={"ck_course_id": ck_ids[0]},
        )
        await client.post(
            "/api/v1/users/me/completed-ck",
            headers=headers_b,
            json={"ck_course_id": ck_ids[1]},
        )

        ck_a = await client.get("/api/v1/users/me/completed-ck", headers=headers_a)
        ck_b = await client.get("/api/v1/users/me/completed-ck", headers=headers_b)
        a_ids = {item["ck_course_id"] for item in ck_a.json()}
        b_ids = {item["ck_course_id"] for item in ck_b.json()}
        assert ck_ids[0] in a_ids and ck_ids[0] not in b_ids
        assert ck_ids[1] in b_ids and ck_ids[1] not in a_ids

        # Рекомендации различаются (разные карьерные цели → разные рекомендации)
        recs_a = await client.get(
            "/api/v1/expert/my-recommendations", headers=headers_a
        )
        recs_b = await client.get(
            "/api/v1/expert/my-recommendations", headers=headers_b
        )
        assert recs_a.status_code == 200
        assert recs_b.status_code == 200
        titles_a = {r["title"] for r in recs_a.json()}
        titles_b = {r["title"] for r in recs_b.json()}
        # Полное совпадение наборов очень маловероятно при разных целях
        assert titles_a != titles_b
