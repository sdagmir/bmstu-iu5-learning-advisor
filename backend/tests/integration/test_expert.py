"""Integration-тесты модуля expert: рекомендации, what-if, debug-trace.

Покрывает три эндпоинта:
- GET  /api/v1/expert/my-recommendations — рекомендации по профилю студента
- POST /api/v1/expert/evaluate           — what-if по произвольному профилю
- POST /api/v1/expert/evaluate/debug     — то же + трассировка (только админ)

Все тесты используют фикстуру `seeded` (правила и компетенции из БД).
"""

from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


# ── Утилиты для подготовки данных ───────────────────────────────────────────


async def _set_profile(
    client: AsyncClient, auth: dict[str, str], **fields: object
) -> None:
    """PATCH /users/me — обновить поля профиля (semester, career_goal и т.д.)."""
    response = await client.patch("/api/v1/users/me", json=fields, headers=auth)
    assert response.status_code == 200, response.text


async def _list_ck_courses(
    client: AsyncClient, auth: dict[str, str]
) -> list[dict[str, object]]:
    """Получить полный каталог ЦК (для добавления пройденных)."""
    response = await client.get("/api/v1/catalog/ck-courses", headers=auth)
    assert response.status_code == 200
    return response.json()


async def _list_disciplines(
    client: AsyncClient, auth: dict[str, str]
) -> list[dict[str, object]]:
    """Полный каталог дисциплин."""
    response = await client.get("/api/v1/catalog/disciplines", headers=auth)
    assert response.status_code == 200
    return response.json()


async def _add_completed_ck(
    client: AsyncClient, auth: dict[str, str], ck_course_id: str
) -> None:
    """POST /users/me/completed-ck — отметить программу как пройденную."""
    response = await client.post(
        "/api/v1/users/me/completed-ck",
        json={"ck_course_id": ck_course_id},
        headers=auth,
    )
    assert response.status_code == 201, response.text


async def _add_completed_ck_by_category(
    client: AsyncClient, auth: dict[str, str], category: str, n: int = 1
) -> int:
    """Добавить N пройденных программ ЦК указанной категории. Вернёт фактически добавленных."""
    courses = await _list_ck_courses(client, auth)
    matching = [c for c in courses if c["category"] == category]
    added = 0
    for c in matching[:n]:
        await _add_completed_ck(client, auth, c["id"])
        added += 1
    return added


async def _set_grades_for_categories(
    client: AsyncClient,
    auth: dict[str, str],
    *,
    grade: int,
    categories: set[str],
) -> int:
    """PUT /users/me/grades — выставить одинаковую оценку всем дисциплинам с
    хотя бы одной компетенцией из заданных категорий. Вернёт число выставленных."""
    disciplines = await _list_disciplines(client, auth)
    entries: list[dict[str, object]] = []
    for d in disciplines:
        comp_categories = {c["category"] for c in d.get("competencies", [])}
        if comp_categories & categories:
            entries.append({"discipline_id": d["id"], "grade": grade})
    response = await client.put(
        "/api/v1/users/me/grades", json={"grades": entries}, headers=auth
    )
    assert response.status_code == 200, response.text
    return len(entries)


def _rule_ids(recs: list[dict[str, object]]) -> set[str]:
    return {r["rule_id"] for r in recs}


def _categories(recs: list[dict[str, object]]) -> set[str]:
    return {r["category"] for r in recs}


# ── 1. GET /api/v1/expert/my-recommendations ────────────────────────────────


class TestMyRecommendations:
    """Сценарии вызова основного эндпоинта с разными профилями студента."""

    async def test_ml_semester_4_no_progress_recommends_ml_engineer(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """ML, 4-й семестр, ничего не пройдено → R1 «Инженер машинного обучения»."""
        await _set_profile(
            client, student_auth, semester=4, career_goal="ml", technopark_status="none"
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert response.status_code == 200
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R1" in ids
        r1 = next(r for r in recs if r["rule_id"] == "R1")
        assert r1["category"] == "ck_course"
        assert r1["priority"] == "high"
        assert "машинного обучения" in r1["title"].lower()

    async def test_ml_with_dev_status_yes_does_not_repeat_dev(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """ML + 2 ЦК категории development → ck_dev_status=YES (X6)."""
        await _set_profile(
            client, student_auth, semester=4, career_goal="ml", technopark_status="none"
        )
        added = await _add_completed_ck_by_category(
            client, student_auth, category="development", n=2
        )
        assert added == 2, "В seed должно быть >=2 ЦК категории development"

        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert response.status_code == 200
        recs = response.json()
        ids = _rule_ids(recs)
        # ML рекомендация (R1) остаётся — она не зависит от dev_status
        assert "R1" in ids
        # Профиль ML не активирует правила про dev (R4-R6, R13, R14)
        assert "R4" not in ids
        assert "R5" not in ids
        assert "R6" not in ids

    async def test_backend_semester_5_recommends_technopark_backend(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """BACKEND, 5-й семестр → срабатывают backend-правила (R4 без dev и др.).

        R23 (ТП бэкенд) активен только для семестров 2-4, поэтому при 5-м
        ожидаем R4 (DevOps как ключевая программа для бэкендера).
        """
        await _set_profile(
            client,
            student_auth,
            semester=5,
            career_goal="backend",
            technopark_status="none",
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        assert response.status_code == 200
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R4" in ids  # backend + dev_status=NO → DevOps
        # На 5 семестре R23 (ТП бэкенд для sem 2-4) НЕ активен
        assert "R23" not in ids

    async def test_backend_semester_3_recommends_technopark_backend(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """BACKEND + 3 семестр + ТП=нет → R23 (вступить в ТП «бэкенд»)."""
        await _set_profile(
            client,
            student_auth,
            semester=3,
            career_goal="backend",
            technopark_status="none",
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R23" in ids
        r23 = next(r for r in recs if r["rule_id"] == "R23")
        assert r23["category"] == "technopark"
        assert r23["priority"] == "high"

    async def test_undecided_semester_2_returns_strategy_without_specific_ck(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """UNDECIDED + 2 семестр → R20 (цифровые навыки) и R47 (стратегия). Без узких ЦК."""
        await _set_profile(
            client,
            student_auth,
            semester=2,
            career_goal="undecided",
            technopark_status="none",
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R20" in ids  # цифровые навыки
        assert "R47" in ids  # стратегия: фокус на базу
        # узкоспециализированные правила по целям не сработали
        assert "R1" not in ids
        assert "R4" not in ids
        assert "R7" not in ids

    async def test_semester_8_high_coverage_triggers_deepening_strategy(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """ML + 8 семестр + завершённые ЦК → высокое покрытие → R49 «углубляться»."""
        await _set_profile(
            client,
            student_auth,
            semester=8,
            career_goal="ml",
            technopark_status="none",
        )
        # Массовая отметка пройденных ЦК для повышения покрытия профиля
        for category in ("ml", "development", "management", "other"):
            await _add_completed_ck_by_category(
                client, student_auth, category=category, n=3
            )
        # И положительные оценки по всем дисциплинам
        await _set_grades_for_categories(
            client,
            student_auth,
            grade=5,
            categories={"math", "programming", "data", "ml", "engineering",
                        "networks", "system", "applied"},
        )

        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        # Высокое покрытие → R49 (углубляться)
        assert "R49" in ids
        # Семестр 8 — ТП не рекомендуется (R27)
        assert "R27" in ids

    async def test_intensive_workload_on_early_semester_triggers_warning(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """workload=INTENSIVE + 1-2 семестр → R46 (предупреждение об интенсивности)."""
        await _set_profile(
            client,
            student_auth,
            semester=2,
            career_goal="ml",
            technopark_status="none",
            workload_pref="intensive",
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R46" in ids
        r46 = next(r for r in recs if r["rule_id"] == "R46")
        assert r46["category"] == "warning"

    async def test_weak_math_for_ml_triggers_math_warning(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """ML + низкие оценки по математическим дисциплинам → R42 (слабая математика)."""
        await _set_profile(
            client,
            student_auth,
            semester=4,
            career_goal="ml",
            technopark_status="none",
        )
        # Двойки по всем дисциплинам с математическими компетенциями
        n_math = await _set_grades_for_categories(
            client, student_auth, grade=2, categories={"math"}
        )
        assert n_math > 0, "В seed должны быть дисциплины с категорией math"

        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R42" in ids
        r42 = next(r for r in recs if r["rule_id"] == "R42")
        assert r42["category"] == "warning"
        assert r42["priority"] == "high"

    async def test_synergy_tp_matches_career_goal(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """TP=ML + cg=ML → R50 (стратегия «синергия»)."""
        await _set_profile(
            client,
            student_auth,
            semester=4,
            career_goal="ml",
            technopark_status="ml",
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        ids = _rule_ids(recs)
        assert "R50" in ids
        r50 = next(r for r in recs if r["rule_id"] == "R50")
        assert r50["category"] == "strategy"

    async def test_recommendation_payload_has_required_fields(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """Каждая рекомендация содержит rule_id, category, title, priority, reasoning."""
        await _set_profile(
            client, student_auth, semester=4, career_goal="ml", technopark_status="none"
        )
        response = await client.get(
            "/api/v1/expert/my-recommendations", headers=student_auth
        )
        recs = response.json()
        assert len(recs) > 0
        for rec in recs:
            assert rec["rule_id"].startswith("R")
            assert rec["category"] in {
                "ck_course",
                "technopark",
                "focus",
                "coursework",
                "warning",
                "strategy",
            }
            assert rec["priority"] in {"high", "medium", "low"}
            assert rec["title"]
            assert rec["reasoning"]

    async def test_unauthenticated_returns_401(
        self,
        client: AsyncClient,
        seeded: None,
    ) -> None:
        response = await client.get("/api/v1/expert/my-recommendations")
        assert response.status_code == 401


# ── 2. POST /api/v1/expert/evaluate (what-if) ────────────────────────────────


class TestEvaluate:
    """What-if: рекомендации по произвольному профилю."""

    async def test_returns_recommendations_for_explicit_profile(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """Передача StudentProfile вручную — рекомендации возвращаются."""
        profile = {
            "user_id": str(uuid.uuid4()),
            "semester": 4,
            "career_goal": "ml",
            "technopark_status": "none",
            "workload_pref": "normal",
            "completed_ck_ml": False,
            "ck_dev_status": "no",
            "completed_ck_security": False,
            "completed_ck_testing": False,
            "weak_math": False,
            "weak_programming": False,
            "coverage": "low",
            "ck_count_in_category": "few",
        }
        response = await client.post(
            "/api/v1/expert/evaluate", json=profile, headers=student_auth
        )
        assert response.status_code == 200
        recs = response.json()
        assert len(recs) > 0
        assert "R1" in _rule_ids(recs)

    async def test_changing_career_goal_changes_recommendations(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """Меняем career_goal в what-if — получаем разные наборы правил."""
        base = {
            "user_id": str(uuid.uuid4()),
            "semester": 4,
            "technopark_status": "none",
            "workload_pref": "normal",
            "completed_ck_ml": False,
            "ck_dev_status": "no",
            "completed_ck_security": False,
            "completed_ck_testing": False,
            "weak_math": False,
            "weak_programming": False,
            "coverage": "low",
            "ck_count_in_category": "few",
        }

        ml_resp = await client.post(
            "/api/v1/expert/evaluate",
            json={**base, "career_goal": "ml"},
            headers=student_auth,
        )
        backend_resp = await client.post(
            "/api/v1/expert/evaluate",
            json={**base, "career_goal": "backend"},
            headers=student_auth,
        )
        assert ml_resp.status_code == 200
        assert backend_resp.status_code == 200

        ml_ids = _rule_ids(ml_resp.json())
        backend_ids = _rule_ids(backend_resp.json())
        assert ml_ids != backend_ids
        assert "R1" in ml_ids and "R1" not in backend_ids
        assert "R4" in backend_ids and "R4" not in ml_ids

    async def test_invalid_semester_returns_422(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """semester вне [1..8] → 422."""
        profile = {
            "user_id": str(uuid.uuid4()),
            "semester": 99,
            "career_goal": "ml",
            "technopark_status": "none",
            "workload_pref": "normal",
        }
        response = await client.post(
            "/api/v1/expert/evaluate", json=profile, headers=student_auth
        )
        assert response.status_code == 422

    async def test_unauthenticated_evaluate_returns_401(
        self, client: AsyncClient, seeded: None
    ) -> None:
        response = await client.post("/api/v1/expert/evaluate", json={})
        assert response.status_code == 401


# ── 3. POST /api/v1/expert/evaluate/debug ────────────────────────────────────


class TestEvaluateDebug:
    """Debug-эндпоинт с трассировкой — только для админа."""

    async def test_student_forbidden(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """Студент не имеет доступа к debug-эндпоинту."""
        profile = {
            "user_id": str(uuid.uuid4()),
            "semester": 4,
            "career_goal": "ml",
            "technopark_status": "none",
            "workload_pref": "normal",
        }
        response = await client.post(
            "/api/v1/expert/evaluate/debug", json=profile, headers=student_auth
        )
        assert response.status_code == 403

    async def test_admin_receives_trace_with_expected_structure(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        seeded: None,
    ) -> None:
        """Админ получает recommendations + полную трассировку правил."""
        profile = {
            "user_id": str(uuid.uuid4()),
            "semester": 4,
            "career_goal": "ml",
            "technopark_status": "none",
            "workload_pref": "normal",
            "completed_ck_ml": False,
            "ck_dev_status": "no",
            "completed_ck_security": False,
            "completed_ck_testing": False,
            "weak_math": False,
            "weak_programming": False,
            "coverage": "low",
            "ck_count_in_category": "few",
        }
        response = await client.post(
            "/api/v1/expert/evaluate/debug", json=profile, headers=admin_auth
        )
        assert response.status_code == 200
        body = response.json()

        # Структура ответа
        assert "recommendations" in body
        assert "trace" in body

        trace = body["trace"]
        assert "profile_snapshot" in trace
        assert "total_checked" in trace
        assert "total_fired" in trace
        assert "fired_rule_ids" in trace
        assert "entries" in trace

        # profile_snapshot — это профиль входа
        snap = trace["profile_snapshot"]
        assert snap["semester"] == 4
        assert snap["career_goal"] == "ml"

        # 50 правил оценено
        assert trace["total_checked"] >= 50
        # Хотя бы одно сработало
        assert trace["total_fired"] >= 1
        assert len(trace["fired_rule_ids"]) == trace["total_fired"]
        # ML/sem4 → R1 точно сработало
        assert "R1" in trace["fired_rule_ids"]

        # Каждая запись trace.entries — словарь с rule, name, group, fired
        for entry in trace["entries"]:
            assert "rule" in entry and entry["rule"].startswith("R")
            assert "name" in entry
            assert "group" in entry
            assert "fired" in entry and isinstance(entry["fired"], bool)

        # Кол-во fired в entries == fired_rule_ids
        fired_in_entries = [e for e in trace["entries"] if e["fired"]]
        assert len(fired_in_entries) == trace["total_fired"]

    async def test_unauthenticated_debug_returns_401(
        self, client: AsyncClient, seeded: None
    ) -> None:
        response = await client.post("/api/v1/expert/evaluate/debug", json={})
        assert response.status_code == 401


# ── 4. Регресс-проверка по всем career_goal ─────────────────────────────────


class TestAllCareerGoalsRegression:
    """Sanity-check: для каждой карьерной цели на 4-м семестре движок выдаёт ≥1 рекомендацию."""

    @pytest.mark.parametrize(
        "career_goal",
        [
            "ml",
            "backend",
            "frontend",
            "cybersecurity",
            "system",
            "devops",
            "mobile",
            "gamedev",
            "qa",
            "analytics",
            "undecided",
        ],
    )
    async def test_returns_non_empty_recommendations(
        self,
        client: AsyncClient,
        student_auth: dict[str, str],
        seeded: None,
        career_goal: str,
    ) -> None:
        profile = {
            "user_id": str(uuid.uuid4()),
            "semester": 4,
            "career_goal": career_goal,
            "technopark_status": "none",
            "workload_pref": "normal",
            "completed_ck_ml": False,
            "ck_dev_status": "no",
            "completed_ck_security": False,
            "completed_ck_testing": False,
            "weak_math": False,
            "weak_programming": False,
            "coverage": "low",
            "ck_count_in_category": "few",
        }
        response = await client.post(
            "/api/v1/expert/evaluate", json=profile, headers=student_auth
        )
        assert response.status_code == 200, f"{career_goal}: {response.text}"
        recs = response.json()
        assert len(recs) > 0, f"Для цели {career_goal} нет ни одной рекомендации"
