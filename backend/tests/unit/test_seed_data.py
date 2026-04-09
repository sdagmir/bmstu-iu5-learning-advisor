"""Тесты seed-данных — валидация всех JSON файлов."""

from __future__ import annotations

import json
from pathlib import Path

from app.db.models import CKCourseCategory, CompetencyCategory, DisciplineType

SEED_DIR = Path(__file__).parent.parent.parent / "app" / "admin" / "seed_data"


def _load(filename: str) -> list[dict]:
    with (SEED_DIR / filename).open(encoding="utf-8") as f:
        return json.load(f)


class TestCompetenciesJSON:
    """Валидация competencies.json."""

    def test_count(self) -> None:
        """38 компетенций."""
        assert len(_load("competencies.json")) == 38

    def test_unique_tags(self) -> None:
        """Все теги уникальны."""
        tags = [c["tag"] for c in _load("competencies.json")]
        assert len(tags) == len(set(tags))

    def test_valid_categories(self) -> None:
        """Все категории валидны."""
        valid = {c.value for c in CompetencyCategory}
        for c in _load("competencies.json"):
            assert c["category"] in valid, f"{c['tag']}: {c['category']}"

    def test_all_categories_used(self) -> None:
        """Все 8 категорий представлены."""
        categories = {c["category"] for c in _load("competencies.json")}
        assert categories == {c.value for c in CompetencyCategory}


class TestCareerDirectionsJSON:
    """Валидация career_directions.json."""

    def test_count(self) -> None:
        """10 направлений."""
        assert len(_load("career_directions.json")) == 10

    def test_unique_names(self) -> None:
        """Все имена уникальны."""
        names = [d["name"] for d in _load("career_directions.json")]
        assert len(names) == len(set(names))

    def test_tags_reference_competencies(self) -> None:
        """Все теги ссылаются на существующие компетенции."""
        comp_tags = {c["tag"] for c in _load("competencies.json")}
        for d in _load("career_directions.json"):
            for tag in d["competency_tags"]:
                assert tag in comp_tags, f"{d['name']}: unknown tag '{tag}'"


class TestCKCoursesJSON:
    """Валидация ck_courses.json."""

    def test_count(self) -> None:
        """20 программ ЦК."""
        assert len(_load("ck_courses.json")) == 20

    def test_unique_names(self) -> None:
        """Все имена уникальны."""
        names = [c["name"] for c in _load("ck_courses.json")]
        assert len(names) == len(set(names))

    def test_valid_categories(self) -> None:
        """Все категории ЦК валидны."""
        valid = {c.value for c in CKCourseCategory}
        for c in _load("ck_courses.json"):
            assert c["category"] in valid, f"{c['name']}: {c['category']}"

    def test_credits_positive(self) -> None:
        """Все кредиты положительные."""
        for c in _load("ck_courses.json"):
            assert c["credits"] >= 1, f"{c['name']}: credits={c['credits']}"

    def test_tags_reference_competencies(self) -> None:
        """Все теги ссылаются на существующие компетенции."""
        comp_tags = {c["tag"] for c in _load("competencies.json")}
        for c in _load("ck_courses.json"):
            for tag in c["competency_tags"] + c["prerequisite_tags"]:
                assert tag in comp_tags, f"{c['name']}: unknown tag '{tag}'"


class TestDisciplinesJSON:
    """Валидация disciplines.json."""

    def test_count(self) -> None:
        """64 дисциплины из учебного плана."""
        assert len(_load("disciplines.json")) == 64

    def test_all_semesters_covered(self) -> None:
        """Дисциплины во всех 8 семестрах."""
        semesters = {d["semester"] for d in _load("disciplines.json")}
        assert semesters == {1, 2, 3, 4, 5, 6, 7, 8}

    def test_valid_types(self) -> None:
        """Все типы дисциплин валидны."""
        valid = {t.value for t in DisciplineType}
        for d in _load("disciplines.json"):
            assert d["type"] in valid, f"{d['name']}: type={d['type']}"

    def test_credits_positive(self) -> None:
        """Все кредиты положительные."""
        for d in _load("disciplines.json"):
            assert d["credits"] >= 1, f"{d['name']}: credits={d['credits']}"

    def test_tags_reference_competencies(self) -> None:
        """Все теги ссылаются на существующие компетенции."""
        comp_tags = {c["tag"] for c in _load("competencies.json")}
        for d in _load("disciplines.json"):
            for tag in d.get("tags", []):
                assert tag in comp_tags, f"{d['name']}: unknown tag '{tag}'"

    def test_mandatory_count(self) -> None:
        """53 обязательных дисциплины."""
        mandatory = [d for d in _load("disciplines.json") if d["type"] == "mandatory"]
        assert len(mandatory) == 53

    def test_semester_1_credits(self) -> None:
        """Семестр 1: 28 е.з. суммарно."""
        sem1 = [d for d in _load("disciplines.json") if d["semester"] == 1]
        assert sum(d["credits"] for d in sem1) == 28


class TestCrossFileConsistency:
    """Кросс-файловая валидация."""

    def test_career_direction_competencies_subset(self) -> None:
        """Теги направлений — подмножество тегов компетенций."""
        all_tags = {c["tag"] for c in _load("competencies.json")}
        for d in _load("career_directions.json"):
            direction_tags = set(d["competency_tags"])
            assert direction_tags <= all_tags, f"{d['name']}: {direction_tags - all_tags}"

    def test_discipline_tags_subset(self) -> None:
        """Теги дисциплин — подмножество тегов компетенций."""
        all_tags = {c["tag"] for c in _load("competencies.json")}
        for d in _load("disciplines.json"):
            disc_tags = set(d.get("tags", []))
            assert disc_tags <= all_tags, f"{d['name']}: {disc_tags - all_tags}"
