"""52 правила ЭС в формате JSON для загрузки в БД.

Каждое правило — словарь с полями:
  number, group, name, description, condition, recommendation, priority

Формат condition:
  {"all": [{"param": "...", "op": "...", "value": ...}, ...]}

Формат recommendation:
  {"category": "...", "title": "...", "priority": "...", "reasoning": "...", "competency_gap": "..."}
"""

from __future__ import annotations

from typing import Any

# Маппинг цель → оптимальное направление ТП (для R28 и R50)
_TP_MAP: dict[str, str | None] = {
    "backend": "backend",
    "frontend": "frontend",
    "ml": "ml",
    "mobile": "mobile",
    "devops": "backend",
    "analytics": "ml",
    "cybersecurity": None,
    "system": None,
    "gamedev": None,
    "qa": None,
    "undecided": None,
}

# Маппинг цель → область курсовой (для R40)
_COURSEWORK_MAP: dict[str, str] = {
    "ml": "машинного обучения и анализа данных",
    "backend": "бэкенд-разработки",
    "frontend": "фронтенд-разработки",
    "cybersecurity": "кибербезопасности",
    "system": "системного программирования",
    "devops": "DevOps и автоматизации инфраструктуры",
    "mobile": "мобильной разработки",
    "gamedev": "разработки компьютерных игр",
    "qa": "тестирования ПО",
    "analytics": "аналитики данных",
    "undecided": "общей разработки ПО",
}


def get_all_rules() -> list[dict[str, Any]]:
    """Возвращает все 52 правила ЭС в JSON-формате."""
    return [
        # ── Группа 1: Программы ЦК по цели (R1-R19) ────────────────────────
        {
            "number": 1,
            "group": "ck_programs",
            "name": "ML: инженер ML",
            "description": "R1: X1=ML И X5=нет И X2≥4 → Инженер машинного обучения (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "completed_ck_ml", "op": "eq", "value": False},
                    {"param": "semester", "op": "gte", "value": 4},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер машинного обучения",
                "priority": "high",
                "reasoning": "Ключевая программа для ML-инженера, закрывает пробел по ML",
                "competency_gap": "ml_basics",
            },
        },
        {
            "number": 2,
            "group": "ck_programs",
            "name": "ML: промпт-инженер",
            "description": "R2: X1=ML И X5=да → Промпт-инженер (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "completed_ck_ml", "op": "eq", "value": True},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Промпт-инженер",
                "priority": "medium",
                "reasoning": "ML-программы пройдены, промпт-инженерия расширит навыки в NLP",
                "competency_gap": "nlp",
            },
        },
        {
            "number": 3,
            "group": "ck_programs",
            "name": "ML: цифровые навыки",
            "description": "R3: X1=ML И X5=нет И X2≤3 → Цифровые навыки (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "completed_ck_ml", "op": "eq", "value": False},
                    {"param": "semester", "op": "lte", "value": 3},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Цифровые навыки",
                "priority": "medium",
                "reasoning": "На ранних семестрах — подготовительная программа перед ML",
                "competency_gap": "python",
            },
        },
        {
            "number": 4,
            "group": "ck_programs",
            "name": "Бэкенд: DevOps",
            "description": "R4: X1=бэкенд И X6=нет → DevOps (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "ck_dev_status", "op": "eq", "value": "no"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер автоматизации разработки и эксплуатации",
                "priority": "high",
                "reasoning": "DevOps — ключевой навык для бэкенд-разработчика",
                "competency_gap": "docker",
            },
        },
        {
            "number": 5,
            "group": "ck_programs",
            "name": "Бэкенд: архитектор",
            "description": "R5: X1=бэкенд И X6=да И X2≥5 → Архитектор платёжных сервисов (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "ck_dev_status", "op": "eq", "value": "yes"},
                    {"param": "semester", "op": "gte", "value": 5},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Архитектор платёжных сервисов",
                "priority": "medium",
                "reasoning": "Углублённая программа по архитектуре для опытного бэкендера",
                "competency_gap": "software_architecture",
            },
        },
        {
            "number": 6,
            "group": "ck_programs",
            "name": "Бэкенд: системный аналитик",
            "description": "R6: X1=бэкенд И X6=частично → Системный аналитик (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "ck_dev_status", "op": "eq", "value": "partial"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Системный аналитик",
                "priority": "medium",
                "reasoning": "Дополнит частично пройденные программы по разработке",
                "competency_gap": "software_architecture",
            },
        },
        {
            "number": 7,
            "group": "ck_programs",
            "name": "Фронтенд: разработчик UI",
            "description": "R7: X1=фронтенд → Разработчик UI (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "frontend"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Разработчик пользовательских интерфейсов",
                "priority": "high",
                "reasoning": "Основная программа для фронтенд-разработчика",
                "competency_gap": "frontend",
            },
        },
        {
            "number": 8,
            "group": "ck_programs",
            "name": "Фронтенд: дизайнер UI",
            "description": "R8: X1=фронтенд И X6=да → Дизайнер UI (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "frontend"},
                    {"param": "ck_dev_status", "op": "eq", "value": "yes"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Дизайнер пользовательских интерфейсов",
                "priority": "medium",
                "reasoning": "Программы по разработке пройдены, UX/UI расширит компетенции",
                "competency_gap": "ux_design",
            },
        },
        {
            "number": 9,
            "group": "ck_programs",
            "name": "Кибербез: ИБ",
            "description": "R9: X1=кибербез И X7=нет → ИБ (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "cybersecurity"},
                    {"param": "completed_ck_security", "op": "eq", "value": False},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Обеспечение информационной безопасности",
                "priority": "high",
                "reasoning": "Базовая программа по ИБ, обязательна для направления",
                "competency_gap": "cryptography",
            },
        },
        {
            "number": 10,
            "group": "ck_programs",
            "name": "Кибербез: пентест",
            "description": "R10: X1=кибербез И X7=да → Пентест (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "cybersecurity"},
                    {"param": "completed_ck_security", "op": "eq", "value": True},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Тестирование на проникновение",
                "priority": "high",
                "reasoning": "Базовая ИБ пройдена, пентест — следующий шаг",
                "competency_gap": "pentesting",
            },
        },
        {
            "number": 11,
            "group": "ck_programs",
            "name": "Кибербез: AppSec",
            "description": "R11: X1=кибербез И X7=да И X2≥6 → AppSec (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "cybersecurity"},
                    {"param": "completed_ck_security", "op": "eq", "value": True},
                    {"param": "semester", "op": "gte", "value": 6},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер по безопасности приложений",
                "priority": "medium",
                "reasoning": "Продвинутая программа по безопасности для старших курсов",
                "competency_gap": "network_security",
            },
        },
        {
            "number": 12,
            "group": "ck_programs",
            "name": "Системное: C/C++",
            "description": "R12: X1=системное → C/C++ (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "system"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Разработка на C и C++",
                "priority": "high",
                "reasoning": "Основная программа для системного программиста",
                "competency_gap": "cpp",
            },
        },
        {
            "number": 13,
            "group": "ck_programs",
            "name": "Системное: встраиваемые",
            "description": "R13: X1=системное И X6=да → Встраиваемые системы (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "system"},
                    {"param": "ck_dev_status", "op": "eq", "value": "yes"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер-разработчик встраиваемых систем",
                "priority": "medium",
                "reasoning": "Программы по разработке пройдены, встраиваемые системы углубят навыки",
                "competency_gap": "computer_architecture",
            },
        },
        {
            "number": 14,
            "group": "ck_programs",
            "name": "DevOps: автоматизация",
            "description": "R14: X1=DevOps И X6=нет → DevOps (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "devops"},
                    {"param": "ck_dev_status", "op": "eq", "value": "no"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер автоматизации разработки и эксплуатации",
                "priority": "high",
                "reasoning": "Ключевая программа для DevOps-инженера",
                "competency_gap": "ci_cd",
            },
        },
        {
            "number": 15,
            "group": "ck_programs",
            "name": "Мобильная: нет программы ЦК",
            "description": "R15: X1=мобильная И (X2<2 ИЛИ X2>4 ИЛИ X3≠нет) → ТП мобильная",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "mobile"},
                    # Не дублирует R26 (который покрывает sem 2-4 + tp=none)
                    {"param": "semester", "op": "not_in", "value": [2, 3, 4]},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Технопарк, направление «мобильная разработка»",
                "priority": "high",
                "reasoning": "Программ ЦК по мобильной разработке нет, Технопарк — основной путь",
                "competency_gap": "mobile_dev",
            },
        },
        {
            "number": 16,
            "group": "ck_programs",
            "name": "Геймдев: игры",
            "description": "R16: X1=геймдев → Разработка игр (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "gamedev"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Разработка компьютерных игр",
                "priority": "high",
                "reasoning": "Основная программа для геймдев-направления",
                "competency_gap": "algorithms",
            },
        },
        {
            "number": 17,
            "group": "ck_programs",
            "name": "Геймдев: C/C++",
            "description": "R17: X1=геймдев И X6=да → C/C++ (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "gamedev"},
                    {"param": "ck_dev_status", "op": "eq", "value": "yes"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Разработка на C и C++",
                "priority": "medium",
                "reasoning": "C/C++ — основа игровых движков, дополнит пройденные программы",
                "competency_gap": "cpp",
            },
        },
        {
            "number": 18,
            "group": "ck_programs",
            "name": "QA: тестирование",
            "description": "R18: X1=QA И X8=нет → Тестирование (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "qa"},
                    {"param": "completed_ck_testing", "op": "eq", "value": False},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Инженер по тестированию производительности",
                "priority": "high",
                "reasoning": "Основная программа для QA-инженера",
                "competency_gap": "testing",
            },
        },
        {
            "number": 19,
            "group": "ck_programs",
            "name": "Аналитика: аналитик",
            "description": "R19: X1=аналитика → Системный аналитик (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "analytics"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Системный аналитик",
                "priority": "medium",
                "reasoning": "Системный анализ — базовая компетенция для аналитика данных",
                "competency_gap": "data_analysis",
            },
        },
        # ── Группа 2: Базовые и универсальные (R20-R22) ─────────────────────
        {
            "number": 20,
            "group": "basic_universal",
            "name": "Не определился: цифровые навыки",
            "description": "R20: X1=не_определился И X2≤3 → Цифровые навыки (высокий)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "undecided"},
                    {"param": "semester", "op": "lte", "value": 3},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Цифровые навыки",
                "priority": "high",
                "reasoning": "Универсальная программа для ранних семестров, пока цель не определена",
                "competency_gap": "python",
            },
        },
        {
            "number": 21,
            "group": "basic_universal",
            "name": "Не определился: low-code",
            "description": "R21: X1=не_определился И X2≥4 → Low-code (средний)",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "undecided"},
                    {"param": "semester", "op": "gte", "value": 4},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Low-code разработка",
                "priority": "medium",
                "reasoning": "Практичная программа, полезна для любого направления",
                "competency_gap": "api_design",
            },
        },
        {
            "number": 22,
            "group": "basic_universal",
            "name": "Диверсификация",
            "description": "R22: X12=много → Программа из другой категории (низкий)",
            "condition": {
                "all": [
                    {"param": "ck_count_in_category", "op": "eq", "value": "many"},
                ]
            },
            "recommendation": {
                "category": "ck_course",
                "title": "Программа из другой категории ЦК",
                "priority": "low",
                "reasoning": "Много программ одной категории — стоит расширить кругозор",
            },
        },
        # ── Группа 3: Технопарк (R23-R28, R51-R52) ─────────────────────────
        {
            "number": 23,
            "group": "technopark",
            "name": "Технопарк: бэкенд",
            "description": "R23: X1=бэкенд И X2∈[2..4] И X3=нет → ТП бэкенд",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «бэкенд-разработка»",
                "priority": "high",
                "reasoning": "Оптимальное время для вступления, направление совпадает с целью",
            },
        },
        {
            "number": 24,
            "group": "technopark",
            "name": "Технопарк: фронтенд",
            "description": "R24: X1=фронтенд И X2∈[2..4] И X3=нет → ТП фронтенд",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "frontend"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «фронтенд-разработка»",
                "priority": "high",
                "reasoning": "Оптимальное время для вступления, направление совпадает с целью",
            },
        },
        {
            "number": 25,
            "group": "technopark",
            "name": "Технопарк: ML",
            "description": "R25: X1=ML И X2∈[2..4] И X3=нет → ТП ML",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «машинное обучение»",
                "priority": "high",
                "reasoning": "Оптимальное время для вступления, направление совпадает с целью",
            },
        },
        {
            "number": 26,
            "group": "technopark",
            "name": "Технопарк: мобильная",
            "description": "R26: X1=мобильная И X2∈[2..4] И X3=нет → ТП мобильная",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "mobile"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «мобильная разработка»",
                "priority": "high",
                "reasoning": "Оптимальное время для вступления, направление совпадает с целью",
            },
        },
        {
            "number": 27,
            "group": "technopark",
            "name": "Технопарк: поздно",
            "description": "R27: X2≥6 И X3=нет → Не рекомендовать ТП",
            "condition": {
                "all": [
                    {"param": "semester", "op": "gte", "value": 6},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Технопарк не рекомендуется",
                "priority": "medium",
                "reasoning": "На 6+ семестре начинать Технопарк поздно — лучше сосредоточиться на ЦК",
            },
        },
        {
            "number": 28,
            "group": "technopark",
            "name": "Технопарк: несоответствие",
            "description": "R28: X3≠нет И X3≠оптимальное_для(X1) → Предупреждение",
            "condition": {
                "all": [
                    {"param": "technopark_status", "op": "neq", "value": "none"},
                    {
                        "param": "technopark_status",
                        "op": "lookup_neq",
                        "value": None,
                        "key_param": "career_goal",
                        "map": _TP_MAP,
                    },
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Несоответствие направления Технопарка и карьерной цели",
                "priority": "medium",
                "reasoning": "Направление ТП не соответствует карьерной цели",
            },
        },
        {
            "number": 51,
            "group": "technopark",
            "name": "Технопарк: DevOps → бэкенд",
            "description": "R51: X1=DevOps И X2∈[2..4] И X3=нет → ТП бэкенд",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "devops"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «бэкенд-разработка»",
                "priority": "high",
                "reasoning": "Направление бэкенд — ближайшее к DevOps в Технопарке",
            },
        },
        {
            "number": 52,
            "group": "technopark",
            "name": "Технопарк: аналитика → ML",
            "description": "R52: X1=аналитика И X2∈[2..4] И X3=нет → ТП ML",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "analytics"},
                    {"param": "semester", "op": "in", "value": [2, 3, 4]},
                    {"param": "technopark_status", "op": "eq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "technopark",
                "title": "Вступить в Технопарк, направление «машинное обучение»",
                "priority": "high",
                "reasoning": "Направление ML — ближайшее к аналитике данных в Технопарке",
            },
        },
        # ── Группа 4: Фокус в дисциплинах (R29-R39) ────────────────────────
        {
            "number": 29,
            "group": "discipline_focus",
            "name": "Фокус: БД для ML",
            "description": "R29: X1=ML И X2∈{4,5}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "semester", "op": "in", "value": [4, 5]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Базы данных: аналитические запросы и оконные функции",
                "priority": "medium",
                "reasoning": "ML-инженеру важны аналитические запросы для работы с данными",
                "competency_gap": "sql",
            },
        },
        {
            "number": 30,
            "group": "discipline_focus",
            "name": "Фокус: БД для бэкенда",
            "description": "R30: X1=бэкенд И X2∈{4,5}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "semester", "op": "in", "value": [4, 5]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Базы данных: проектирование схем, нормализация, индексы",
                "priority": "medium",
                "reasoning": "Бэкенд-разработчику критично владеть проектированием БД",
                "competency_gap": "db_design",
            },
        },
        {
            "number": 31,
            "group": "discipline_focus",
            "name": "Фокус: ООП для ML",
            "description": "R31: X1=ML И X2∈{2,3}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "semester", "op": "in", "value": [2, 3]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "ООП: паттерны Pipeline и Strategy",
                "priority": "medium",
                "reasoning": "Pipeline и Strategy — основа ML-фреймворков",
                "competency_gap": "design_patterns",
            },
        },
        {
            "number": 32,
            "group": "discipline_focus",
            "name": "Фокус: ООП для бэкенда",
            "description": "R32: X1=бэкенд И X2∈{2,3}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "semester", "op": "in", "value": [2, 3]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "ООП: SOLID, Repository, Factory, Observer",
                "priority": "medium",
                "reasoning": "Паттерны проектирования — фундамент бэкенд-архитектуры",
                "competency_gap": "design_patterns",
            },
        },
        {
            "number": 33,
            "group": "discipline_focus",
            "name": "Фокус: сети для кибербеза",
            "description": "R33: X1=кибербез И X2∈{5,6}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "cybersecurity"},
                    {"param": "semester", "op": "in", "value": [5, 6]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Сети: уязвимости протоколов, анализ трафика, Wireshark",
                "priority": "medium",
                "reasoning": "Анализ сетевого трафика — ключевой навык кибербезопасника",
                "competency_gap": "network_protocols",
            },
        },
        {
            "number": 34,
            "group": "discipline_focus",
            "name": "Фокус: сети для DevOps",
            "description": "R34: X1=DevOps И X2∈{5,6}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "devops"},
                    {"param": "semester", "op": "in", "value": [5, 6]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Сети: DNS, балансировка, сетевые пространства Docker",
                "priority": "medium",
                "reasoning": "DevOps-инженеру важно понимать сетевую инфраструктуру",
                "competency_gap": "networking",
            },
        },
        {
            "number": 35,
            "group": "discipline_focus",
            "name": "Фокус: теорвер для ML",
            "description": "R35: X1=ML И X2∈{3,4}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "semester", "op": "in", "value": [3, 4]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Теория вероятностей: байесовский подход, распределения",
                "priority": "medium",
                "reasoning": "Теорвер — математический фундамент машинного обучения",
                "competency_gap": "probability",
            },
        },
        {
            "number": 36,
            "group": "discipline_focus",
            "name": "Фокус: ОС для системщика",
            "description": "R36: X1=системное И X2∈{5,6}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "system"},
                    {"param": "semester", "op": "in", "value": [5, 6]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "ОС: ядро, системные вызовы, управление памятью",
                "priority": "medium",
                "reasoning": "Глубокое понимание ОС — основа системного программирования",
                "competency_gap": "operating_systems",
            },
        },
        {
            "number": 37,
            "group": "discipline_focus",
            "name": "Фокус: ОС для DevOps",
            "description": "R37: X1=DevOps И X2∈{5,6}",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "devops"},
                    {"param": "semester", "op": "in", "value": [5, 6]},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "ОС: cgroups, namespaces, контейнеризация на уровне ядра",
                "priority": "medium",
                "reasoning": "Понимание механизмов контейнеризации на уровне ядра",
                "competency_gap": "operating_systems",
            },
        },
        {
            "number": 38,
            "group": "discipline_focus",
            "name": "Фокус: сетевые технологии для бэкенда",
            "description": "R38: X1=бэкенд И X2=6",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "backend"},
                    {"param": "semester", "op": "eq", "value": 6},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Сетевые технологии: REST API, микросервисы, межсервисное взаимодействие",
                "priority": "medium",
                "reasoning": "Ключевые навыки для бэкенд-разработки на старших курсах",
                "competency_gap": "api_design",
            },
        },
        {
            "number": 39,
            "group": "discipline_focus",
            "name": "Фокус: интернет-приложения для фронтенда",
            "description": "R39: X1=фронтенд И X2=6",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "frontend"},
                    {"param": "semester", "op": "eq", "value": 6},
                ]
            },
            "recommendation": {
                "category": "focus",
                "title": "Разработка интернет-приложений: SPA-архитектура, компонентный подход",
                "priority": "medium",
                "reasoning": "SPA и компонентный подход — основа современного фронтенда",
                "competency_gap": "frontend",
            },
        },
        # ── Группа 5: Курсовые (R40-R41) ───────────────────────────────────
        {
            "number": 40,
            "group": "coursework",
            "name": "Курсовая по цели",
            "description": "R40: X2∈{4,5,6,7} → Тема курсовой в области X1",
            "condition": {
                "all": [
                    {"param": "semester", "op": "in", "value": [4, 5, 6, 7]},
                ]
            },
            "recommendation": {
                "category": "coursework",
                "title": "Тема курсовой в области {career_goal_area}",
                "priority": "medium",
                "reasoning": "Курсовая в области {career_goal_area} укрепит портфолио по целевому направлению",
                "mappings": {
                    "career_goal_area": {
                        "from_param": "career_goal",
                        "map": _COURSEWORK_MAP,
                        "default": "разработки ПО",
                    },
                },
            },
        },
        {
            "number": 41,
            "group": "coursework",
            "name": "Курсовая: диверсификация",
            "description": "R41: X2=7 → Смежная область для портфолио",
            "condition": {
                "all": [
                    {"param": "semester", "op": "eq", "value": 7},
                ]
            },
            "recommendation": {
                "category": "coursework",
                "title": "Курсовая в смежной области для расширения портфолио",
                "priority": "low",
                "reasoning": "К 7-му семестру основные курсовые уже были — стоит расширить спектр",
            },
        },
        # ── Группа 6: Предупреждения (R42-R46) ─────────────────────────────
        {
            "number": 42,
            "group": "warnings",
            "name": "Предупреждение: математика для ML",
            "description": "R42: X1=ML И X9=да",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "ml"},
                    {"param": "weak_math", "op": "eq", "value": True},
                ]
            },
            "recommendation": {
                "category": "warning",
                "title": "Слабая база по математике для программы ML",
                "priority": "high",
                "reasoning": "Программа ML опирается на линейную алгебру и теорию вероятностей",
                "competency_gap": "linear_algebra",
            },
        },
        {
            "number": 43,
            "group": "warnings",
            "name": "Предупреждение: математика для аналитики",
            "description": "R43: X1=аналитика И X9=да",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "eq", "value": "analytics"},
                    {"param": "weak_math", "op": "eq", "value": True},
                ]
            },
            "recommendation": {
                "category": "warning",
                "title": "Слабая база по математике для аналитики",
                "priority": "high",
                "reasoning": "Аналитика данных требует статистику и теорию вероятностей",
                "competency_gap": "statistics",
            },
        },
        {
            "number": 44,
            "group": "warnings",
            "name": "Предупреждение: программирование",
            "description": "R44: X1∈{ML,бэкенд,DevOps} И X10=да",
            "condition": {
                "all": [
                    {"param": "career_goal", "op": "in", "value": ["ml", "backend", "devops"]},
                    {"param": "weak_programming", "op": "eq", "value": True},
                ]
            },
            "recommendation": {
                "category": "warning",
                "title": "Слабая база по программированию для выбранного направления",
                "priority": "high",
                "reasoning": "Выбранное направление требует уверенного владения программированием",
                "competency_gap": "python",
            },
        },
        {
            "number": 45,
            "group": "warnings",
            "name": "Предупреждение: нагрузка ТП",
            "description": "R45: X4=лёгкая И X3≠нет",
            "condition": {
                "all": [
                    {"param": "workload_pref", "op": "eq", "value": "light"},
                    {"param": "technopark_status", "op": "neq", "value": "none"},
                ]
            },
            "recommendation": {
                "category": "warning",
                "title": "Риск перегруза при лёгкой нагрузке",
                "priority": "medium",
                "reasoning": "Технопарк + программы ЦК при желании лёгкой нагрузки — риск перегруза",
            },
        },
        {
            "number": 46,
            "group": "warnings",
            "name": "Предупреждение: интенсив на ранних",
            "description": "R46: X4=интенсивная И X2∈{1,2}",
            "condition": {
                "all": [
                    {"param": "workload_pref", "op": "eq", "value": "intensive"},
                    {"param": "semester", "op": "in", "value": [1, 2]},
                ]
            },
            "recommendation": {
                "category": "warning",
                "title": "Интенсивная нагрузка на ранних семестрах рискованна",
                "priority": "medium",
                "reasoning": "На 1-2 семестрах важно адаптироваться, не перегружаться сразу",
            },
        },
        # ── Группа 7: Стратегия (R47-R50) ──────────────────────────────────
        {
            "number": 47,
            "group": "strategy",
            "name": "Стратегия: ранний семестр",
            "description": "R47: X2∈{1,2}",
            "condition": {
                "all": [
                    {"param": "semester", "op": "in", "value": [1, 2]},
                ]
            },
            "recommendation": {
                "category": "strategy",
                "title": "Фокус на базу: математика и программирование",
                "priority": "medium",
                "reasoning": "На ранних семестрах приоритет — фундаментальные дисциплины",
            },
        },
        {
            "number": 48,
            "group": "strategy",
            "name": "Стратегия: мало времени, низкое покрытие",
            "description": "R48: X2≥6 И X11=низкое",
            "condition": {
                "all": [
                    {"param": "semester", "op": "gte", "value": 6},
                    {"param": "coverage", "op": "eq", "value": "low"},
                ]
            },
            "recommendation": {
                "category": "strategy",
                "title": "Интенсивный план: максимум программ ЦК по целевым пробелам",
                "priority": "high",
                "reasoning": "Мало семестров осталось при низком покрытии — нужен интенсивный план",
            },
        },
        {
            "number": 49,
            "group": "strategy",
            "name": "Стратегия: высокое покрытие",
            "description": "R49: X11=высокое",
            "condition": {
                "all": [
                    {"param": "coverage", "op": "eq", "value": "high"},
                ]
            },
            "recommendation": {
                "category": "strategy",
                "title": "Профиль почти собран — углубляться в специализацию",
                "priority": "medium",
                "reasoning": "Покрытие целевого профиля высокое, пора углубляться, а не расширяться",
            },
        },
        {
            "number": 50,
            "group": "strategy",
            "name": "Стратегия: синергия",
            "description": "R50: X3 совпадает с оптимальным для X1",
            "condition": {
                "all": [
                    {"param": "technopark_status", "op": "neq", "value": "none"},
                    {
                        "param": "technopark_status",
                        "op": "lookup_eq",
                        "value": None,
                        "key_param": "career_goal",
                        "map": _TP_MAP,
                    },
                ]
            },
            "recommendation": {
                "category": "strategy",
                "title": "Удачная комбинация: Технопарк + ЦК + цель в одном направлении",
                "priority": "medium",
                "reasoning": "Направление Технопарка совпадает с карьерной целью — синергия",
            },
        },
    ]
