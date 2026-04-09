"""Построитель профиля студента — вычисляет X5-X12 из данных БД.

X1-X4 задаются студентом (career_goal, semester, technopark_status, workload_pref).
X5-X12 вычисляются автоматически из пройденных ЦК и оценок по дисциплинам.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import (
    CareerDirection,
    CareerGoal,
    CKCourse,
    CKCourseCategory,
    CompetencyCategory,
    Discipline,
    StudentCompletedCK,
    StudentGrade,
    TechparkStatus,
    WorkloadPref,
)
from app.expert.schemas import (
    CKCategoryCount,
    CKDevStatus,
    CoverageLevel,
    StudentProfile,
)

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.db.models import User

# Порог средней оценки: ниже → считается слабым направлением
WEAK_THRESHOLD = 4.0

# Маппинг CareerGoal → имя CareerDirection (из seed-данных)
_GOAL_TO_DIRECTION_NAME: dict[CareerGoal, str] = {
    CareerGoal.ML: "ML / Data Science",
    CareerGoal.BACKEND: "Бэкенд-разработка",
    CareerGoal.FRONTEND: "Фронтенд-разработка",
    CareerGoal.CYBERSECURITY: "Кибербезопасность",
    CareerGoal.SYSTEM: "Системное программирование",
    CareerGoal.DEVOPS: "DevOps / Инфраструктура",
    CareerGoal.MOBILE: "Мобильная разработка",
    CareerGoal.GAMEDEV: "Геймдев",
    CareerGoal.QA: "QA / Тестирование",
    CareerGoal.ANALYTICS: "Аналитика данных / BI",
}


async def build_student_profile(user: User, db: AsyncSession) -> StudentProfile:
    """Построить полный профиль студента (X1-X12) из данных в БД."""
    user_id = user.id
    semester = user.semester or 1
    career_goal = CareerGoal(user.career_goal) if user.career_goal else CareerGoal.UNDECIDED
    technopark_status = (
        TechparkStatus(user.technopark_status) if user.technopark_status else TechparkStatus.NONE
    )
    workload_pref = (
        WorkloadPref(user.workload_pref) if user.workload_pref else WorkloadPref.NORMAL
    )

    # Загрузка пройденных ЦК с категориями
    completed_courses = await _load_completed_ck(user_id, db)
    category_counts = Counter(c.category for c in completed_courses)

    # X5: есть пройденные ЦК по ML
    completed_ck_ml = category_counts.get(CKCourseCategory.ML, 0) > 0

    # X6: статус ЦК по разработке (0 → no, 1 → partial, 2+ → yes)
    dev_count = category_counts.get(CKCourseCategory.DEVELOPMENT, 0)
    if dev_count == 0:
        ck_dev_status = CKDevStatus.NO
    elif dev_count == 1:
        ck_dev_status = CKDevStatus.PARTIAL
    else:
        ck_dev_status = CKDevStatus.YES

    # X7: есть пройденные ЦК по безопасности
    completed_ck_security = category_counts.get(CKCourseCategory.SECURITY, 0) > 0

    # X8: есть пройденные ЦК по тестированию
    completed_ck_testing = category_counts.get(CKCourseCategory.TESTING, 0) > 0

    # X9, X10: по средней оценке в категории < WEAK_THRESHOLD
    weak_math, weak_programming = await _compute_weak_flags(user_id, db)

    # X11: покрытие целевого профиля компетенций
    coverage = await _compute_coverage(
        user_id, career_goal, semester, completed_courses, db
    )

    # X12: максимум ЦК в одной категории >= 3 → many
    max_in_category = max(category_counts.values()) if category_counts else 0
    ck_count_in_category = CKCategoryCount.MANY if max_in_category >= 3 else CKCategoryCount.FEW

    return StudentProfile(
        user_id=user_id,
        semester=semester,
        career_goal=career_goal,
        technopark_status=technopark_status,
        workload_pref=workload_pref,
        completed_ck_ml=completed_ck_ml,
        ck_dev_status=ck_dev_status,
        completed_ck_security=completed_ck_security,
        completed_ck_testing=completed_ck_testing,
        weak_math=weak_math,
        weak_programming=weak_programming,
        coverage=coverage,
        ck_count_in_category=ck_count_in_category,
    )


async def _load_completed_ck(user_id: uuid.UUID, db: AsyncSession) -> list[CKCourse]:
    """Загрузить курсы ЦК, пройденные студентом."""
    result = await db.execute(
        select(CKCourse)
        .join(StudentCompletedCK, CKCourse.id == StudentCompletedCK.ck_course_id)
        .where(StudentCompletedCK.user_id == user_id)
    )
    return list(result.scalars().all())


async def _compute_weak_flags(
    user_id: uuid.UUID, db: AsyncSession
) -> tuple[bool, bool]:
    """Вычислить X9 (weak_math) и X10 (weak_programming) по средней оценке.

    Средняя оценка по дисциплинам с мат./прогр. компетенциями < WEAK_THRESHOLD → True.
    Если оценок в категории нет → False (нет данных = не слабый).
    """
    result = await db.execute(
        select(StudentGrade)
        .options(selectinload(StudentGrade.discipline).selectinload(Discipline.competencies))
        .where(StudentGrade.user_id == user_id)
    )
    student_grades = list(result.scalars().all())

    math_grades: list[int] = []
    programming_grades: list[int] = []

    for sg in student_grades:
        categories = {comp.category for comp in sg.discipline.competencies}
        if CompetencyCategory.MATH in categories:
            math_grades.append(sg.grade)
        if CompetencyCategory.PROGRAMMING in categories:
            programming_grades.append(sg.grade)

    weak_math = (sum(math_grades) / len(math_grades) < WEAK_THRESHOLD) if math_grades else False
    weak_prog = (
        (sum(programming_grades) / len(programming_grades) < WEAK_THRESHOLD)
        if programming_grades
        else False
    )

    return weak_math, weak_prog


async def _compute_coverage(
    user_id: uuid.UUID,
    career_goal: CareerGoal,
    semester: int,
    completed_courses: list[CKCourse],
    db: AsyncSession,
) -> CoverageLevel:
    """Вычислить X11 — покрытие целевого профиля компетенций.

    Формула: (компетенции студента ∩ целевые) / целевые
    Компетенции студента = из дисциплин до текущего семестра + из пройденных ЦК.
    Дисциплины с оценкой ≤ 2 (неудовлетворительно) не считаются освоенными.
    """
    if career_goal == CareerGoal.UNDECIDED:
        return CoverageLevel.LOW

    direction_name = _GOAL_TO_DIRECTION_NAME.get(career_goal)
    if not direction_name:
        return CoverageLevel.LOW

    # Целевые компетенции карьерного направления
    result = await db.execute(
        select(CareerDirection)
        .options(selectinload(CareerDirection.competencies))
        .where(CareerDirection.name == direction_name)
    )
    direction = result.scalar_one_or_none()
    if not direction or not direction.competencies:
        return CoverageLevel.LOW

    target_ids = {c.id for c in direction.competencies}

    # Дисциплины с оценкой ≤ 2 — не считаем освоенными
    result = await db.execute(
        select(StudentGrade.discipline_id)
        .where(StudentGrade.user_id == user_id, StudentGrade.grade <= 2)
    )
    failed_discipline_ids = {row[0] for row in result.all()}

    # Компетенции из дисциплин до текущего семестра (включительно)
    student_comp_ids: set[uuid.UUID] = set()

    result = await db.execute(
        select(Discipline)
        .options(selectinload(Discipline.competencies))
        .where(Discipline.semester <= semester)
    )
    disciplines = list(result.scalars().unique().all())

    for disc in disciplines:
        if disc.id not in failed_discipline_ids:
            for comp in disc.competencies:
                student_comp_ids.add(comp.id)

    # Компетенции из пройденных ЦК
    if completed_courses:
        course_ids = [c.id for c in completed_courses]
        result = await db.execute(
            select(CKCourse)
            .options(selectinload(CKCourse.competencies))
            .where(CKCourse.id.in_(course_ids))
        )
        courses_with_comps = list(result.scalars().unique().all())
        for course in courses_with_comps:
            for comp in course.competencies:
                student_comp_ids.add(comp.id)

    # Вычисление покрытия
    overlap = len(student_comp_ids & target_ids)
    ratio = overlap / len(target_ids)

    if ratio > 0.7:
        return CoverageLevel.HIGH
    if ratio >= 0.3:
        return CoverageLevel.MEDIUM
    return CoverageLevel.LOW
