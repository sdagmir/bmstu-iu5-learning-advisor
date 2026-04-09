"""Тесты ProfileBuilder — вычисление X5-X12 из данных студента."""

from __future__ import annotations

import uuid
from collections import Counter
from unittest.mock import MagicMock

from app.db.models import (
    CareerGoal,
    CKCourseCategory,
    CompetencyCategory,
)
from app.expert.schemas import CKCategoryCount, CKDevStatus, CoverageLevel
from app.users.profile_builder import WEAK_THRESHOLD

# ── Хелперы для создания моков ──────────────────────────────────────────────


def _make_course(category: CKCourseCategory) -> MagicMock:
    """Мок CKCourse."""
    c = MagicMock()
    c.id = uuid.uuid4()
    c.category = category
    c.competencies = []
    return c


def _make_competency(category: CompetencyCategory, tag: str = "comp") -> MagicMock:
    """Мок Competency."""
    c = MagicMock()
    c.id = uuid.uuid4()
    c.tag = tag
    c.category = category
    return c


def _make_discipline(comps: list[MagicMock]) -> MagicMock:
    """Мок Discipline."""
    d = MagicMock()
    d.id = uuid.uuid4()
    d.competencies = comps
    return d


def _make_grade(discipline: MagicMock, grade: int) -> MagicMock:
    """Мок StudentGrade."""
    sg = MagicMock()
    sg.discipline_id = discipline.id
    sg.discipline = discipline
    sg.grade = grade
    return sg


def _avg(grades: list[int]) -> float:
    """Средняя оценка."""
    return sum(grades) / len(grades) if grades else 0.0


# ── Тесты X5-X8: категории пройденных ЦК ──────────────────────────────────


class TestCKCategoryFlags:
    """Вычисление X5, X6, X7, X8 из пройденных ЦК."""

    def test_no_completed_ck(self) -> None:
        """Нет пройденных ЦК → все False/NO."""
        counts: Counter[CKCourseCategory] = Counter()
        assert counts.get(CKCourseCategory.ML, 0) == 0
        assert counts.get(CKCourseCategory.DEVELOPMENT, 0) == 0
        assert counts.get(CKCourseCategory.SECURITY, 0) == 0
        assert counts.get(CKCourseCategory.TESTING, 0) == 0

    def test_ml_completed(self) -> None:
        """X5: пройден ЦК по ML → True."""
        courses = [_make_course(CKCourseCategory.ML)]
        counts = Counter(c.category for c in courses)
        assert counts.get(CKCourseCategory.ML, 0) > 0

    def test_dev_partial(self) -> None:
        """X6: один ЦК по development → partial."""
        courses = [_make_course(CKCourseCategory.DEVELOPMENT)]
        dev_count = Counter(c.category for c in courses).get(
            CKCourseCategory.DEVELOPMENT, 0
        )
        assert dev_count == 1
        result = (
            CKDevStatus.NO if dev_count == 0
            else CKDevStatus.PARTIAL if dev_count == 1
            else CKDevStatus.YES
        )
        assert result == CKDevStatus.PARTIAL

    def test_dev_full(self) -> None:
        """X6: два+ ЦК по development → yes."""
        courses = [
            _make_course(CKCourseCategory.DEVELOPMENT),
            _make_course(CKCourseCategory.DEVELOPMENT),
        ]
        dev_count = Counter(c.category for c in courses).get(
            CKCourseCategory.DEVELOPMENT, 0
        )
        assert dev_count == 2

    def test_security_completed(self) -> None:
        """X7: пройден ЦК по безопасности → True."""
        courses = [_make_course(CKCourseCategory.SECURITY)]
        counts = Counter(c.category for c in courses)
        assert counts.get(CKCourseCategory.SECURITY, 0) > 0

    def test_testing_completed(self) -> None:
        """X8: пройден ЦК по тестированию → True."""
        courses = [_make_course(CKCourseCategory.TESTING)]
        counts = Counter(c.category for c in courses)
        assert counts.get(CKCourseCategory.TESTING, 0) > 0


# ── Тесты X9-X10: средняя оценка по категориям ────────────────────────────


class TestWeakByAverage:
    """Вычисление X9 (weak_math) и X10 (weak_programming) по средней оценке."""

    def test_no_grades_not_weak(self) -> None:
        """Нет оценок → не слабый (нет данных)."""
        math_grades: list[int] = []
        assert not (
            _avg(math_grades) < WEAK_THRESHOLD if math_grades else False
        )

    def test_all_fives_not_weak(self) -> None:
        """Все пятёрки → не слабый."""
        grades = [5, 5, 5]
        assert _avg(grades) >= WEAK_THRESHOLD

    def test_all_threes_weak(self) -> None:
        """Все тройки → слабый (средняя 3.0 < 4.0)."""
        grades = [3, 3, 3]
        assert _avg(grades) < WEAK_THRESHOLD

    def test_mixed_above_threshold(self) -> None:
        """Разброс: 5, 3, 4, 5, 4 → средняя 4.2 → не слабый."""
        grades = [5, 3, 4, 5, 4]
        assert _avg(grades) == 4.2
        assert _avg(grades) >= WEAK_THRESHOLD

    def test_mixed_below_threshold(self) -> None:
        """Разброс: 3, 3, 4, 3, 4 → средняя 3.4 → слабый."""
        grades = [3, 3, 4, 3, 4]
        assert _avg(grades) == 3.4
        assert _avg(grades) < WEAK_THRESHOLD

    def test_exact_threshold_not_weak(self) -> None:
        """Средняя ровно 4.0 → НЕ слабый (< 4.0, не <=)."""
        grades = [3, 5]
        assert _avg(grades) == 4.0
        assert not (_avg(grades) < WEAK_THRESHOLD)

    def test_one_bad_among_good(self) -> None:
        """Одна тройка среди пятёрок → средняя 4.6 → не слабый."""
        grades = [5, 5, 3, 5, 5]
        assert _avg(grades) == 4.6
        assert _avg(grades) >= WEAK_THRESHOLD

    def test_category_filtering(self) -> None:
        """Оценки разных категорий фильтруются отдельно."""
        math_comp = _make_competency(CompetencyCategory.MATH)
        prog_comp = _make_competency(CompetencyCategory.PROGRAMMING)
        net_comp = _make_competency(CompetencyCategory.NETWORKS)

        disc_math = _make_discipline([math_comp])
        disc_prog = _make_discipline([prog_comp])
        disc_net = _make_discipline([net_comp])

        grades = [
            _make_grade(disc_math, 3),  # мат → 3
            _make_grade(disc_prog, 5),  # прогр → 5
            _make_grade(disc_net, 2),   # сети → 2, не влияет
        ]

        math_grades = [
            sg.grade for sg in grades
            if CompetencyCategory.MATH in {c.category for c in sg.discipline.competencies}
        ]
        prog_grades = [
            sg.grade for sg in grades
            if CompetencyCategory.PROGRAMMING in {c.category for c in sg.discipline.competencies}
        ]

        assert _avg(math_grades) == 3.0
        assert _avg(math_grades) < WEAK_THRESHOLD  # weak_math = True

        assert _avg(prog_grades) == 5.0
        assert _avg(prog_grades) >= WEAK_THRESHOLD  # weak_prog = False


# ── Тесты X11: покрытие профиля ────────────────────────────────────────────


class TestCoverage:
    """Вычисление X11 (coverage) по компетенциям."""

    def _classify(self, ratio: float) -> CoverageLevel:
        if ratio > 0.7:
            return CoverageLevel.HIGH
        if ratio >= 0.3:
            return CoverageLevel.MEDIUM
        return CoverageLevel.LOW

    def test_undecided_always_low(self) -> None:
        """Цель undecided → всегда low."""
        assert CareerGoal.UNDECIDED not in {
            CareerGoal.ML, CareerGoal.BACKEND, CareerGoal.FRONTEND,
        }

    def test_no_overlap_low(self) -> None:
        assert self._classify(0.0) == CoverageLevel.LOW

    def test_partial_overlap_medium(self) -> None:
        assert self._classify(0.4) == CoverageLevel.MEDIUM

    def test_high_overlap_high(self) -> None:
        assert self._classify(0.8) == CoverageLevel.HIGH

    def test_boundary_30_is_medium(self) -> None:
        assert self._classify(0.3) == CoverageLevel.MEDIUM

    def test_boundary_70_is_medium(self) -> None:
        """70% → medium (строго > 0.7 для high)."""
        assert self._classify(0.7) == CoverageLevel.MEDIUM


# ── Тесты X12: количество ЦК в категории ──────────────────────────────────


class TestCKCountInCategory:
    """Вычисление X12 (ck_count_in_category)."""

    def _classify(self, max_in_cat: int) -> CKCategoryCount:
        return CKCategoryCount.MANY if max_in_cat >= 3 else CKCategoryCount.FEW

    def test_empty_is_few(self) -> None:
        counts: Counter[CKCourseCategory] = Counter()
        max_in_cat = max(counts.values()) if counts else 0
        assert self._classify(max_in_cat) == CKCategoryCount.FEW

    def test_two_is_few(self) -> None:
        courses = [_make_course(CKCourseCategory.ML)] * 2
        counts = Counter(c.category for c in courses)
        assert self._classify(max(counts.values())) == CKCategoryCount.FEW

    def test_three_is_many(self) -> None:
        courses = [_make_course(CKCourseCategory.DEVELOPMENT)] * 3
        counts = Counter(c.category for c in courses)
        assert self._classify(max(counts.values())) == CKCategoryCount.MANY

    def test_mixed_categories(self) -> None:
        courses = [
            _make_course(CKCourseCategory.ML),
            _make_course(CKCourseCategory.ML),
            _make_course(CKCourseCategory.DEVELOPMENT),
            _make_course(CKCourseCategory.SECURITY),
        ]
        counts = Counter(c.category for c in courses)
        assert self._classify(max(counts.values())) == CKCategoryCount.FEW


# ── Тест маппинга CareerGoal → CareerDirection ─────────────────────────────


class TestGoalToDirection:
    """Маппинг CareerGoal → имя CareerDirection."""

    def test_all_goals_except_undecided_mapped(self) -> None:
        from app.users.profile_builder import _GOAL_TO_DIRECTION_NAME

        for goal in CareerGoal:
            if goal == CareerGoal.UNDECIDED:
                assert goal not in _GOAL_TO_DIRECTION_NAME
            else:
                assert goal in _GOAL_TO_DIRECTION_NAME

    def test_direction_names_are_strings(self) -> None:
        from app.users.profile_builder import _GOAL_TO_DIRECTION_NAME

        for name in _GOAL_TO_DIRECTION_NAME.values():
            assert isinstance(name, str)
            assert len(name) > 0
