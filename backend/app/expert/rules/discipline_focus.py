from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
)
from app.expert.registry import rule
from app.expert.schemas import Recommendation, StudentProfile

# ── Группа 4: Фокус в обязательных дисциплинах (11 правил, R29-R39) ──────────


@rule(
    number=29,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: БД для ML",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r29_focus_db_ml(profile: StudentProfile) -> Recommendation | None:
    """R29: X1=ML И X2∈{4,5} → БД: аналитические запросы, оконные функции"""
    if profile.career_goal == CareerGoal.ML and profile.semester in {4, 5}:
        return Recommendation(
            rule_id="R29",
            category=RecommendationCategory.FOCUS,
            title="Базы данных: аналитические запросы и оконные функции",
            priority=RecommendationPriority.MEDIUM,
            reasoning="ML-инженеру важны аналитические запросы для работы с данными",
            competency_gap="sql",
        )
    return None


@rule(
    number=30,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: БД для бэкенда",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r30_focus_db_backend(profile: StudentProfile) -> Recommendation | None:
    """R30: X1=бэкенд И X2∈{4,5} → БД: проектирование схем, нормализация, индексы"""
    if profile.career_goal == CareerGoal.BACKEND and profile.semester in {4, 5}:
        return Recommendation(
            rule_id="R30",
            category=RecommendationCategory.FOCUS,
            title="Базы данных: проектирование схем, нормализация, индексы",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Бэкенд-разработчику критично владеть проектированием БД",
            competency_gap="db_design",
        )
    return None


@rule(
    number=31,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: ООП для ML",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r31_focus_oop_ml(profile: StudentProfile) -> Recommendation | None:
    """R31: X1=ML И X2∈{2,3} → ООП: паттерны Pipeline и Strategy"""
    if profile.career_goal == CareerGoal.ML and profile.semester in {2, 3}:
        return Recommendation(
            rule_id="R31",
            category=RecommendationCategory.FOCUS,
            title="ООП: паттерны Pipeline и Strategy",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Pipeline и Strategy — основа ML-фреймворков",
            competency_gap="design_patterns",
        )
    return None


@rule(
    number=32,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: ООП для бэкенда",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r32_focus_oop_backend(profile: StudentProfile) -> Recommendation | None:
    """R32: X1=бэкенд И X2∈{2,3} → ООП: SOLID, Repository, Factory, Observer"""
    if profile.career_goal == CareerGoal.BACKEND and profile.semester in {2, 3}:
        return Recommendation(
            rule_id="R32",
            category=RecommendationCategory.FOCUS,
            title="ООП: SOLID, Repository, Factory, Observer",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Паттерны проектирования — фундамент бэкенд-архитектуры",
            competency_gap="design_patterns",
        )
    return None


@rule(
    number=33,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: сети для кибербеза",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r33_focus_networks_cyber(profile: StudentProfile) -> Recommendation | None:
    """R33: X1=кибербез И X2∈{5,6} → Сети: уязвимости протоколов, Wireshark"""
    if profile.career_goal == CareerGoal.CYBERSECURITY and profile.semester in {5, 6}:
        return Recommendation(
            rule_id="R33",
            category=RecommendationCategory.FOCUS,
            title="Сети: уязвимости протоколов, анализ трафика, Wireshark",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Анализ сетевого трафика — ключевой навык кибербезопасника",
            competency_gap="network_protocols",
        )
    return None


@rule(
    number=34,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: сети для DevOps",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r34_focus_networks_devops(profile: StudentProfile) -> Recommendation | None:
    """R34: X1=DevOps И X2∈{5,6} → Сети: DNS, балансировка, сетевые пространства"""
    if profile.career_goal == CareerGoal.DEVOPS and profile.semester in {5, 6}:
        return Recommendation(
            rule_id="R34",
            category=RecommendationCategory.FOCUS,
            title="Сети: DNS, балансировка, сетевые пространства Docker",
            priority=RecommendationPriority.MEDIUM,
            reasoning="DevOps-инженеру важно понимать сетевую инфраструктуру",
            competency_gap="networking",
        )
    return None


@rule(
    number=35,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: теорвер для ML",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r35_focus_probability_ml(profile: StudentProfile) -> Recommendation | None:
    """R35: X1=ML И X2∈{3,4} → Теорвер: байесовский подход, распределения"""
    if profile.career_goal == CareerGoal.ML and profile.semester in {3, 4}:
        return Recommendation(
            rule_id="R35",
            category=RecommendationCategory.FOCUS,
            title="Теория вероятностей: байесовский подход, распределения",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Теорвер — математический фундамент машинного обучения",
            competency_gap="probability",
        )
    return None


@rule(
    number=36,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: ОС для системщика",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r36_focus_os_system(profile: StudentProfile) -> Recommendation | None:
    """R36: X1=системное И X2∈{5,6} → ОС: ядро, системные вызовы, управление памятью"""
    if profile.career_goal == CareerGoal.SYSTEM and profile.semester in {5, 6}:
        return Recommendation(
            rule_id="R36",
            category=RecommendationCategory.FOCUS,
            title="ОС: ядро, системные вызовы, управление памятью",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Глубокое понимание ОС — основа системного программирования",
            competency_gap="operating_systems",
        )
    return None


@rule(
    number=37,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: ОС для DevOps",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r37_focus_os_devops(profile: StudentProfile) -> Recommendation | None:
    """R37: X1=DevOps И X2∈{5,6} → ОС: cgroups, namespaces, контейнеризация"""
    if profile.career_goal == CareerGoal.DEVOPS and profile.semester in {5, 6}:
        return Recommendation(
            rule_id="R37",
            category=RecommendationCategory.FOCUS,
            title="ОС: cgroups, namespaces, контейнеризация на уровне ядра",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Понимание механизмов контейнеризации на уровне ядра",
            competency_gap="operating_systems",
        )
    return None


@rule(
    number=38,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: сетевые технологии для бэкенда",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r38_focus_net_tech_backend(profile: StudentProfile) -> Recommendation | None:
    """R38: X1=бэкенд И X2=6 → REST API, микросервисы, межсервисное взаимодействие"""
    if profile.career_goal == CareerGoal.BACKEND and profile.semester == 6:
        return Recommendation(
            rule_id="R38",
            category=RecommendationCategory.FOCUS,
            title="Сетевые технологии: REST API, микросервисы, межсервисное взаимодействие",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Ключевые навыки для бэкенд-разработки на старших курсах",
            competency_gap="api_design",
        )
    return None


@rule(
    number=39,
    group=RuleGroup.DISCIPLINE_FOCUS,
    name="Фокус: интернет-приложения для фронтенда",
    output_param=RecommendationCategory.FOCUS,
    input_params=("X1", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r39_focus_web_frontend(profile: StudentProfile) -> Recommendation | None:
    """R39: X1=фронтенд И X2=6 → SPA-архитектура, компонентный подход"""
    if profile.career_goal == CareerGoal.FRONTEND and profile.semester == 6:
        return Recommendation(
            rule_id="R39",
            category=RecommendationCategory.FOCUS,
            title="Разработка интернет-приложений: SPA-архитектура, компонентный подход",
            priority=RecommendationPriority.MEDIUM,
            reasoning="SPA и компонентный подход — основа современного фронтенда",
            competency_gap="frontend",
        )
    return None
