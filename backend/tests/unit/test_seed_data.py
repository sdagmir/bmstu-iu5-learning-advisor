"""Тесты seed-данных — валидация disciplines.json."""

from __future__ import annotations

import json
from pathlib import Path

from app.db.models import DisciplineType

SEED_DIR = Path(__file__).parent.parent.parent / "app" / "admin" / "seed_data"

# Все теги из seed компетенций
VALID_TAGS = {
    "python", "cpp", "javascript", "git", "linux", "algorithms",
    "linear_algebra", "calculus", "discrete_math", "probability", "statistics",
    "sql", "db_design", "data_analysis", "data_visualization",
    "ml_basics", "deep_learning", "nlp", "computer_vision",
    "oop", "design_patterns", "api_design", "docker", "ci_cd",
    "testing", "software_architecture",
    "networking", "network_protocols", "cryptography", "pentesting", "network_security",
    "computer_architecture", "operating_systems", "parallel_computing",
    "mobile_dev", "frontend", "ux_design", "game_dev",
}


class TestDisciplinesJSON:
    """Валидация файла disciplines.json."""

    def _load(self) -> list[dict]:
        with (SEED_DIR / "disciplines.json").open(encoding="utf-8") as f:
            return json.load(f)

    def test_file_loads(self) -> None:
        """JSON файл загружается без ошибок."""
        data = self._load()
        assert len(data) > 0

    def test_total_count(self) -> None:
        """64 дисциплины из учебного плана."""
        assert len(self._load()) == 64

    def test_all_semesters_covered(self) -> None:
        """Дисциплины во всех 8 семестрах."""
        semesters = {d["semester"] for d in self._load()}
        assert semesters == {1, 2, 3, 4, 5, 6, 7, 8}

    def test_valid_types(self) -> None:
        """Все типы дисциплин валидны."""
        valid = {t.value for t in DisciplineType}
        for d in self._load():
            assert d["type"] in valid, f"{d['name']}: type={d['type']}"

    def test_credits_positive(self) -> None:
        """Все кредиты положительные."""
        for d in self._load():
            assert d["credits"] >= 1, f"{d['name']}: credits={d['credits']}"

    def test_tags_exist_in_competencies(self) -> None:
        """Все теги ссылаются на существующие компетенции."""
        for d in self._load():
            for tag in d.get("tags", []):
                assert tag in VALID_TAGS, f"{d['name']}: unknown tag '{tag}'"

    def test_mandatory_count(self) -> None:
        """53 обязательных дисциплины."""
        mandatory = [d for d in self._load() if d["type"] == "mandatory"]
        assert len(mandatory) == 53

    def test_semester_1_credits(self) -> None:
        """Семестр 1: суммарные е.з. совпадают с учебным планом."""
        sem1 = [d for d in self._load() if d["semester"] == 1]
        total = sum(d["credits"] for d in sem1)
        assert total == 28  # 4+2+5+3+3+2+3+6
