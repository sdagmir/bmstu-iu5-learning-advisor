"""Интерпретатор условий правил ЭС.

Вычисляет JSON-условия из БД по профилю студента.
Поддерживаемые операторы: eq, neq, gt, gte, lt, lte, in, not_in, lookup_neq.

Формат условий:
    {"all": [{"param": "career_goal", "op": "eq", "value": "ml"}, ...]}
    {"any": [{"param": ..., "op": ..., "value": ...}, ...]}

Каждое условие — объект с полями:
    - param: имя поля StudentProfile (например "career_goal", "semester")
    - op: оператор сравнения
    - value: ожидаемое значение
    - map (только для lookup_neq): словарь маппинга
"""

from __future__ import annotations

from typing import Any


def evaluate_condition(condition: dict[str, Any], profile_data: dict[str, Any]) -> bool:
    """Вычислить JSON-условие по данным профиля.

    Возвращает True если условие выполнено.
    """
    if "all" in condition:
        return all(_evaluate_single(c, profile_data) for c in condition["all"])
    if "any" in condition:
        return any(_evaluate_single(c, profile_data) for c in condition["any"])
    # Одиночное условие без обёртки
    return _evaluate_single(condition, profile_data)


def _evaluate_single(cond: dict[str, Any], profile: dict[str, Any]) -> bool:
    """Вычислить одно элементарное условие."""
    param = cond["param"]
    op = cond["op"]
    expected = cond["value"]

    actual = profile.get(param)
    if actual is None:
        return False

    if op == "eq":
        return actual == expected
    if op == "neq":
        return actual != expected
    if op == "gt":
        return actual > expected
    if op == "gte":
        return actual >= expected
    if op == "lt":
        return actual < expected
    if op == "lte":
        return actual <= expected
    if op == "in":
        return actual in expected
    if op == "not_in":
        return actual not in expected
    if op == "lookup_neq":
        # Проверка: значение из маппинга по ключу param_key не равно actual другого поля
        # Используется для R28 (Технопарк: несоответствие) и R50 (синергия)
        lookup_map: dict[str, Any] = cond["map"]
        key_param = cond["key_param"]
        key_value = profile.get(key_param)
        mapped = lookup_map.get(str(key_value))
        return mapped is not None and actual != mapped
    if op == "lookup_eq":
        # Обратная проверка: значение из маппинга по ключу совпадает с actual
        lookup_map = cond["map"]
        key_param = cond["key_param"]
        key_value = profile.get(key_param)
        mapped = lookup_map.get(str(key_value))
        return mapped is not None and actual == mapped

    msg = f"Неизвестный оператор: {op}"
    raise ValueError(msg)
