from __future__ import annotations

from app.db.models import (
    CareerGoal,
    RecommendationCategory,
    RecommendationPriority,
    RuleGroup,
)
from app.expert.registry import rule
from app.expert.schemas import CKDevStatus, Recommendation, StudentProfile

# ── Группа 1: Рекомендации по программам ЦК (19 правил, R1-R19) ─────────────


@rule(
    number=1,
    group=RuleGroup.CK_PROGRAMS,
    name="ML: инженер ML",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X5", "X2"),
    priority=RecommendationPriority.HIGH,
)
def r01_ml_engineer(profile: StudentProfile) -> Recommendation | None:
    """R1: X1=ML И X5=нет И X2≥4 → Инженер машинного обучения (высокий)"""
    if (
        profile.career_goal == CareerGoal.ML
        and not profile.completed_ck_ml
        and profile.semester >= 4
    ):
        return Recommendation(
            rule_id="R1",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер машинного обучения",
            priority=RecommendationPriority.HIGH,
            reasoning="Ключевая программа для ML-инженера, закрывает пробел по ML",
            competency_gap="ml_basics",
        )
    return None


@rule(
    number=2,
    group=RuleGroup.CK_PROGRAMS,
    name="ML: промпт-инженер",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X5"),
    priority=RecommendationPriority.MEDIUM,
)
def r02_ml_prompt(profile: StudentProfile) -> Recommendation | None:
    """R2: X1=ML И X5=да → Промпт-инженер (средний)"""
    if profile.career_goal == CareerGoal.ML and profile.completed_ck_ml:
        return Recommendation(
            rule_id="R2",
            category=RecommendationCategory.CK_COURSE,
            title="Промпт-инженер",
            priority=RecommendationPriority.MEDIUM,
            reasoning="ML-программы пройдены, промпт-инженерия расширит навыки в NLP",
            competency_gap="nlp",
        )
    return None


@rule(
    number=3,
    group=RuleGroup.CK_PROGRAMS,
    name="ML: цифровые навыки",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X5", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r03_ml_digital_basics(profile: StudentProfile) -> Recommendation | None:
    """R3: X1=ML И X5=нет И X2≤3 → Цифровые навыки как подготовка (средний)"""
    if (
        profile.career_goal == CareerGoal.ML
        and not profile.completed_ck_ml
        and profile.semester <= 3
    ):
        return Recommendation(
            rule_id="R3",
            category=RecommendationCategory.CK_COURSE,
            title="Цифровые навыки",
            priority=RecommendationPriority.MEDIUM,
            reasoning="На ранних семестрах — подготовительная программа перед ML",
            competency_gap="python",
        )
    return None


@rule(
    number=4,
    group=RuleGroup.CK_PROGRAMS,
    name="Бэкенд: DevOps",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.HIGH,
)
def r04_backend_devops(profile: StudentProfile) -> Recommendation | None:
    """R4: X1=бэкенд И X6=нет → Инженер автоматизации разработки (высокий)"""
    if profile.career_goal == CareerGoal.BACKEND and profile.ck_dev_status == CKDevStatus.NO:
        return Recommendation(
            rule_id="R4",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер автоматизации разработки и эксплуатации",
            priority=RecommendationPriority.HIGH,
            reasoning="DevOps — ключевой навык для бэкенд-разработчика",
            competency_gap="docker",
        )
    return None


@rule(
    number=5,
    group=RuleGroup.CK_PROGRAMS,
    name="Бэкенд: архитектор",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r05_backend_architect(profile: StudentProfile) -> Recommendation | None:
    """R5: X1=бэкенд И X6=да И X2≥5 → Архитектор платежных сервисов (средний)"""
    if (
        profile.career_goal == CareerGoal.BACKEND
        and profile.ck_dev_status == CKDevStatus.YES
        and profile.semester >= 5
    ):
        return Recommendation(
            rule_id="R5",
            category=RecommendationCategory.CK_COURSE,
            title="Архитектор платёжных сервисов",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Углублённая программа по архитектуре для опытного бэкендера",
            competency_gap="software_architecture",
        )
    return None


@rule(
    number=6,
    group=RuleGroup.CK_PROGRAMS,
    name="Бэкенд: системный аналитик",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.MEDIUM,
)
def r06_backend_analyst(profile: StudentProfile) -> Recommendation | None:
    """R6: X1=бэкенд И X6=частично → Системный аналитик (средний)"""
    if profile.career_goal == CareerGoal.BACKEND and profile.ck_dev_status == CKDevStatus.PARTIAL:
        return Recommendation(
            rule_id="R6",
            category=RecommendationCategory.CK_COURSE,
            title="Системный аналитик",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Дополнит частично пройденные программы по разработке",
            competency_gap="software_architecture",
        )
    return None


@rule(
    number=7,
    group=RuleGroup.CK_PROGRAMS,
    name="Фронтенд: разработчик UI",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1",),
    priority=RecommendationPriority.HIGH,
)
def r07_frontend_ui_dev(profile: StudentProfile) -> Recommendation | None:
    """R7: X1=фронтенд → Разработчик пользовательских интерфейсов (высокий)"""
    if profile.career_goal == CareerGoal.FRONTEND:
        return Recommendation(
            rule_id="R7",
            category=RecommendationCategory.CK_COURSE,
            title="Разработчик пользовательских интерфейсов",
            priority=RecommendationPriority.HIGH,
            reasoning="Основная программа для фронтенд-разработчика",
            competency_gap="frontend",
        )
    return None


@rule(
    number=8,
    group=RuleGroup.CK_PROGRAMS,
    name="Фронтенд: дизайнер UI",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.MEDIUM,
)
def r08_frontend_ui_design(profile: StudentProfile) -> Recommendation | None:
    """R8: X1=фронтенд И X6=да → Дизайнер пользовательских интерфейсов (средний)"""
    if profile.career_goal == CareerGoal.FRONTEND and profile.ck_dev_status == CKDevStatus.YES:
        return Recommendation(
            rule_id="R8",
            category=RecommendationCategory.CK_COURSE,
            title="Дизайнер пользовательских интерфейсов",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Программы по разработке пройдены, UX/UI расширит компетенции",
            competency_gap="ux_design",
        )
    return None


@rule(
    number=9,
    group=RuleGroup.CK_PROGRAMS,
    name="Кибербез: ИБ",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X7"),
    priority=RecommendationPriority.HIGH,
)
def r09_cyber_ib(profile: StudentProfile) -> Recommendation | None:
    """R9: X1=кибербез И X7=нет → Обеспечение информационной безопасности (высокий)"""
    if profile.career_goal == CareerGoal.CYBERSECURITY and not profile.completed_ck_security:
        return Recommendation(
            rule_id="R9",
            category=RecommendationCategory.CK_COURSE,
            title="Обеспечение информационной безопасности",
            priority=RecommendationPriority.HIGH,
            reasoning="Базовая программа по ИБ, обязательна для направления",
            competency_gap="cryptography",
        )
    return None


@rule(
    number=10,
    group=RuleGroup.CK_PROGRAMS,
    name="Кибербез: пентест",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X7"),
    priority=RecommendationPriority.HIGH,
)
def r10_cyber_pentest(profile: StudentProfile) -> Recommendation | None:
    """R10: X1=кибербез И X7=да → Тестирование на проникновение (высокий)"""
    if profile.career_goal == CareerGoal.CYBERSECURITY and profile.completed_ck_security:
        return Recommendation(
            rule_id="R10",
            category=RecommendationCategory.CK_COURSE,
            title="Тестирование на проникновение",
            priority=RecommendationPriority.HIGH,
            reasoning="Базовая ИБ пройдена, пентест — следующий шаг",
            competency_gap="pentesting",
        )
    return None


@rule(
    number=11,
    group=RuleGroup.CK_PROGRAMS,
    name="Кибербез: AppSec",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X7", "X2"),
    priority=RecommendationPriority.MEDIUM,
)
def r11_cyber_appsec(profile: StudentProfile) -> Recommendation | None:
    """R11: X1=кибербез И X7=да И X2≥6 → Инженер по безопасности приложений (средний)"""
    if (
        profile.career_goal == CareerGoal.CYBERSECURITY
        and profile.completed_ck_security
        and profile.semester >= 6
    ):
        return Recommendation(
            rule_id="R11",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер по безопасности приложений",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Продвинутая программа по безопасности для старших курсов",
            competency_gap="network_security",
        )
    return None


@rule(
    number=12,
    group=RuleGroup.CK_PROGRAMS,
    name="Системное: C/C++",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1",),
    priority=RecommendationPriority.HIGH,
)
def r12_system_cpp(profile: StudentProfile) -> Recommendation | None:
    """R12: X1=системное → Разработка на C и C++ (высокий)"""
    if profile.career_goal == CareerGoal.SYSTEM:
        return Recommendation(
            rule_id="R12",
            category=RecommendationCategory.CK_COURSE,
            title="Разработка на C и C++",
            priority=RecommendationPriority.HIGH,
            reasoning="Основная программа для системного программиста",
            competency_gap="cpp",
        )
    return None


@rule(
    number=13,
    group=RuleGroup.CK_PROGRAMS,
    name="Системное: встраиваемые",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.MEDIUM,
)
def r13_system_embedded(profile: StudentProfile) -> Recommendation | None:
    """R13: X1=системное И X6=да → Инженер-разработчик встраиваемых систем (средний)"""
    if profile.career_goal == CareerGoal.SYSTEM and profile.ck_dev_status == CKDevStatus.YES:
        return Recommendation(
            rule_id="R13",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер-разработчик встраиваемых систем",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Программы по разработке пройдены, встраиваемые системы углубят навыки",
            competency_gap="computer_architecture",
        )
    return None


@rule(
    number=14,
    group=RuleGroup.CK_PROGRAMS,
    name="DevOps: автоматизация",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.HIGH,
)
def r14_devops_automation(profile: StudentProfile) -> Recommendation | None:
    """R14: X1=DevOps И X6=нет → Инженер автоматизации разработки (высокий)"""
    if profile.career_goal == CareerGoal.DEVOPS and profile.ck_dev_status == CKDevStatus.NO:
        return Recommendation(
            rule_id="R14",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер автоматизации разработки и эксплуатации",
            priority=RecommendationPriority.HIGH,
            reasoning="Ключевая программа для DevOps-инженера",
            competency_gap="ci_cd",
        )
    return None


@rule(
    number=15,
    group=RuleGroup.CK_PROGRAMS,
    name="Мобильная: нет программы ЦК",
    output_param=RecommendationCategory.TECHNOPARK,
    input_params=("X1",),
    priority=RecommendationPriority.HIGH,
)
def r15_mobile_no_ck(profile: StudentProfile) -> Recommendation | None:
    """R15: X1=мобильная → Программ ЦК по мобильной нет, рекомендовать ТП мобильная.

    Примечание: пропускает, когда R26 (Технопарк: мобильная) сработает, чтобы избежать дубля.
    """
    if profile.career_goal != CareerGoal.MOBILE:
        return None
    # R26 покрывает семестры 2-4 при ТП=нет — пропускаем, чтобы избежать дубля
    from app.db.models import TechparkStatus

    if 2 <= profile.semester <= 4 and profile.technopark_status == TechparkStatus.NONE:
        return None
    if profile.career_goal == CareerGoal.MOBILE:
        return Recommendation(
            rule_id="R15",
            category=RecommendationCategory.TECHNOPARK,
            title="Технопарк, направление «мобильная разработка»",
            priority=RecommendationPriority.HIGH,
            reasoning="Программ ЦК по мобильной разработке нет, Технопарк — основной путь",
            competency_gap="mobile_dev",
        )
    return None


@rule(
    number=16,
    group=RuleGroup.CK_PROGRAMS,
    name="Геймдев: игры",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1",),
    priority=RecommendationPriority.HIGH,
)
def r16_gamedev_games(profile: StudentProfile) -> Recommendation | None:
    """R16: X1=геймдев → Разработка компьютерных игр (высокий)"""
    if profile.career_goal == CareerGoal.GAMEDEV:
        return Recommendation(
            rule_id="R16",
            category=RecommendationCategory.CK_COURSE,
            title="Разработка компьютерных игр",
            priority=RecommendationPriority.HIGH,
            reasoning="Основная программа для геймдев-направления",
            competency_gap="algorithms",
        )
    return None


@rule(
    number=17,
    group=RuleGroup.CK_PROGRAMS,
    name="Геймдев: C/C++",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X6"),
    priority=RecommendationPriority.MEDIUM,
)
def r17_gamedev_cpp(profile: StudentProfile) -> Recommendation | None:
    """R17: X1=геймдев И X6=да → Разработка на C и C++ (средний)"""
    if profile.career_goal == CareerGoal.GAMEDEV and profile.ck_dev_status == CKDevStatus.YES:
        return Recommendation(
            rule_id="R17",
            category=RecommendationCategory.CK_COURSE,
            title="Разработка на C и C++",
            priority=RecommendationPriority.MEDIUM,
            reasoning="C/C++ — основа игровых движков, дополнит пройденные программы",
            competency_gap="cpp",
        )
    return None


@rule(
    number=18,
    group=RuleGroup.CK_PROGRAMS,
    name="QA: тестирование",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1", "X8"),
    priority=RecommendationPriority.HIGH,
)
def r18_qa_testing(profile: StudentProfile) -> Recommendation | None:
    """R18: X1=QA И X8=нет → Инженер по тестированию производительности (высокий)"""
    if profile.career_goal == CareerGoal.QA and not profile.completed_ck_testing:
        return Recommendation(
            rule_id="R18",
            category=RecommendationCategory.CK_COURSE,
            title="Инженер по тестированию производительности",
            priority=RecommendationPriority.HIGH,
            reasoning="Основная программа для QA-инженера",
            competency_gap="testing",
        )
    return None


@rule(
    number=19,
    group=RuleGroup.CK_PROGRAMS,
    name="Аналитика: аналитик",
    output_param=RecommendationCategory.CK_COURSE,
    input_params=("X1",),
    priority=RecommendationPriority.MEDIUM,
)
def r19_analytics_analyst(profile: StudentProfile) -> Recommendation | None:
    """R19: X1=аналитика → Системный аналитик (средний)"""
    if profile.career_goal == CareerGoal.ANALYTICS:
        return Recommendation(
            rule_id="R19",
            category=RecommendationCategory.CK_COURSE,
            title="Системный аналитик",
            priority=RecommendationPriority.MEDIUM,
            reasoning="Системный анализ — базовая компетенция для аналитика данных",
            competency_gap="data_analysis",
        )
    return None
