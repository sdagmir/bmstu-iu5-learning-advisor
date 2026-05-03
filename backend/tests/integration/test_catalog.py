"""Integration-тесты модуля catalog: дисциплины и программы ЦК."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


class TestDisciplines:
    async def test_list_disciplines_no_filter(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Без фильтра возвращаются все 64 дисциплины."""
        response = await client.get(
            "/api/v1/catalog/disciplines", headers=student_auth
        )
        assert response.status_code == 200
        items = response.json()
        # >= 64: admin-тесты могут добавить дисциплины в seed-таблицы (не очищаются между файлами)
        assert len(items) >= 64

    async def test_disciplines_sorted_by_semester(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Дисциплины отсортированы по семестру (по возрастанию)."""
        response = await client.get(
            "/api/v1/catalog/disciplines", headers=student_auth
        )
        items = response.json()
        semesters = [item["semester"] for item in items]
        assert semesters == sorted(semesters)

    async def test_discipline_fields_shape(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Каждая дисциплина содержит все обязательные поля."""
        response = await client.get(
            "/api/v1/catalog/disciplines", headers=student_auth
        )
        items = response.json()
        sample = items[0]
        for field in (
            "id",
            "name",
            "semester",
            "credits",
            "type",
            "control_form",
            "department",
            "competencies",
        ):
            assert field in sample
        assert isinstance(sample["competencies"], list)
        assert sample["type"] in ("mandatory", "elective", "choice")

    async def test_discipline_competency_short_shape(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Поля CompetencyShort внутри дисциплины (если есть привязки)."""
        response = await client.get(
            "/api/v1/catalog/disciplines", headers=student_auth
        )
        items = response.json()
        with_comps = [it for it in items if it["competencies"]]
        if with_comps:
            comp = with_comps[0]["competencies"][0]
            assert "id" in comp
            assert "tag" in comp
            assert "name" in comp
            assert "category" in comp

    async def test_filter_semester_max_two(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Фильтр semester_max=2 — только семестры 1 и 2."""
        response = await client.get(
            "/api/v1/catalog/disciplines?semester_max=2", headers=student_auth
        )
        assert response.status_code == 200
        items = response.json()
        assert len(items) > 0
        for item in items:
            assert item["semester"] <= 2

    async def test_filter_semester_max_eight_returns_all(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """semester_max=8 возвращает все дисциплины."""
        response = await client.get(
            "/api/v1/catalog/disciplines?semester_max=8", headers=student_auth
        )
        assert response.status_code == 200
        assert len(response.json()) >= 64

    async def test_filter_semester_max_zero_returns_422(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """semester_max=0 отклоняется (ge=1)."""
        response = await client.get(
            "/api/v1/catalog/disciplines?semester_max=0", headers=student_auth
        )
        assert response.status_code == 422

    async def test_filter_semester_max_too_large_returns_422(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """semester_max=99 отклоняется (le=8)."""
        response = await client.get(
            "/api/v1/catalog/disciplines?semester_max=99", headers=student_auth
        )
        assert response.status_code == 422


class TestCKCourses:
    async def test_list_ck_courses(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Возвращаются все 20 программ ЦК."""
        response = await client.get(
            "/api/v1/catalog/ck-courses", headers=student_auth
        )
        assert response.status_code == 200
        items = response.json()
        assert len(items) >= 20

    async def test_ck_course_fields_shape(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """Каждый ЦК-курс содержит все обязательные поля."""
        response = await client.get(
            "/api/v1/catalog/ck-courses", headers=student_auth
        )
        items = response.json()
        sample = items[0]
        for field in (
            "id",
            "name",
            "description",
            "category",
            "credits",
            "competencies",
            "prerequisites",
        ):
            assert field in sample
        assert isinstance(sample["competencies"], list)
        assert isinstance(sample["prerequisites"], list)
        assert sample["category"] in (
            "ml",
            "development",
            "security",
            "testing",
            "management",
            "other",
        )
        assert isinstance(sample["credits"], int)

    async def test_ck_course_categories_present(
        self, client: AsyncClient, student_auth: dict[str, str], seeded: None
    ) -> None:
        """В выдаче встречаются разные категории."""
        response = await client.get(
            "/api/v1/catalog/ck-courses", headers=student_auth
        )
        categories = {item["category"] for item in response.json()}
        # сид содержит несколько категорий — минимум 2
        assert len(categories) >= 2
