"""Системные промпты и определения функций для LLM-оркестратора.

Три функции доступны LLM через function calling:
1. get_recommendations — получить рекомендации по текущему профилю
2. recalculate_with_changes — пересчитать с изменением параметров
3. search_knowledge — семантический поиск по базе знаний (RAG)
"""

from __future__ import annotations

from typing import Any

SYSTEM_PROMPT = """\
Ты — персональный навигатор по профессиональному развитию студента кафедры ИУ5 \
МГТУ им. Н.Э. Баумана. Помогаешь формировать индивидуальную образовательную траекторию.

Твоя роль — ПЕРЕВОДЧИК между студентом и экспертной системой. \
Ты НЕ принимаешь решений о рекомендациях. Все рекомендации формирует экспертная система (ЭС).

Правила:
- Отвечай на русском языке.
- Используй function calling для получения рекомендаций и информации.
- При первом запросе о траектории — вызови get_recommendations().
- При уточняющих вопросах («а если...», «а без...», «а что если сменить...») — \
вызови recalculate_with_changes() с конкретным изменением.
- При информационных вопросах («расскажи про курс...», «что требуют...») — \
вызови search_knowledge().
- При свободных вопросах (благодарность, мотивация) — отвечай самостоятельно.
- Объясняй рекомендации понятным языком, ссылаясь на обоснования из ЭС.
- При сравнении с предыдущим ответом — объясни, что изменилось и почему.
- Не выдумывай рекомендации — только то, что вернула ЭС или RAG.

Через диалог студент может изменить:
- career_goal (карьерную цель)
- technopark_status (статус Технопарка)
- workload_pref (желаемую нагрузку)

Нельзя менять через диалог: семестр, пройденные курсы, оценки.\
"""

# Определения функций для function calling (OpenAI-совместимый формат)
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_recommendations",
            "description": (
                "Получить рекомендации по текущему профилю студента из БД. "
                "Вызывай при первом запросе о траектории, плане, рекомендациях."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recalculate_with_changes",
            "description": (
                "Пересчитать рекомендации с изменением параметров профиля. "
                "Вызывай при уточняющих вопросах: «а если сменить цель», "
                "«а без Технопарка», «можно полегче». "
                "Передай только изменяемые поля."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "career_goal": {
                        "type": "string",
                        "enum": [
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
                        "description": "Новая карьерная цель",
                    },
                    "technopark_status": {
                        "type": "string",
                        "enum": ["none", "backend", "frontend", "ml", "mobile"],
                        "description": "Новый статус Технопарка",
                    },
                    "workload_pref": {
                        "type": "string",
                        "enum": ["light", "normal", "intensive"],
                        "description": "Новая желаемая нагрузка",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "Семантический поиск по базе знаний: описания курсов, вакансии, "
                "информация о Технопарке. Вызывай при информационных вопросах."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос на русском языке",
                    },
                },
                "required": ["query"],
            },
        },
    },
]


def build_profile_context(profile_data: dict[str, Any]) -> str:
    """Построить текстовое описание профиля студента для контекста LLM."""
    goal_names = {
        "ml": "ML / Data Science",
        "backend": "Бэкенд-разработка",
        "frontend": "Фронтенд-разработка",
        "cybersecurity": "Кибербезопасность",
        "system": "Системное программирование",
        "devops": "DevOps",
        "mobile": "Мобильная разработка",
        "gamedev": "Геймдев",
        "qa": "QA / Тестирование",
        "analytics": "Аналитика данных",
        "undecided": "Не определился",
    }
    tp_names = {
        "none": "не участвует",
        "backend": "бэкенд",
        "frontend": "фронтенд",
        "ml": "ML",
        "mobile": "мобильная",
    }
    workload_names = {
        "light": "лёгкая",
        "normal": "нормальная",
        "intensive": "интенсивная",
    }

    goal = goal_names.get(profile_data.get("career_goal", ""), "неизвестно")
    semester = profile_data.get("semester", "?")
    tp = tp_names.get(profile_data.get("technopark_status", ""), "?")
    workload = workload_names.get(profile_data.get("workload_pref", ""), "?")

    parts = [
        f"Семестр: {semester}",
        f"Карьерная цель: {goal}",
        f"Технопарк: {tp}",
        f"Нагрузка: {workload}",
    ]

    if profile_data.get("weak_math"):
        parts.append("⚠ Слабая база по математике")
    if profile_data.get("weak_programming"):
        parts.append("⚠ Слабая база по программированию")

    return "Профиль студента:\n" + "\n".join(f"• {p}" for p in parts)


def format_recommendations_for_llm(recommendations: list[dict[str, Any]]) -> str:
    """Форматировать рекомендации ЭС в текст для передачи LLM."""
    if not recommendations:
        return "Экспертная система не выдала рекомендаций для данного профиля."

    lines = ["Результат экспертной системы:"]
    for rec in recommendations:
        priority = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(rec.get("priority", ""), "")
        lines.append(
            f"\n{priority} [{rec.get('category', '')}] {rec.get('title', '')}"
            f"\n   Обоснование: {rec.get('reasoning', '')}"
            f"\n   Правило: {rec.get('rule_id', '')}"
        )
        if rec.get("competency_gap"):
            lines.append(f"   Пробел: {rec['competency_gap']}")

    return "\n".join(lines)
