from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models import RecommendationCategory, RecommendationPriority, RuleGroup
    from app.expert.schemas import Recommendation, StudentProfile

RuleFunc = Callable[["StudentProfile"], "Recommendation | None"]

# Порядок вычисления групп (соответствует таблице в документации)
_GROUP_ORDER: dict[str, int] = {
    "ck_programs": 0,
    "basic_universal": 1,
    "technopark": 2,
    "discipline_focus": 3,
    "coursework": 4,
    "warnings": 5,
    "strategy": 6,
}


@dataclass(frozen=True, slots=True)
class RuleSpec:
    """Метаданные и вызываемая функция одного правила."""

    number: int
    group: RuleGroup
    name: str
    func: RuleFunc
    output_param: RecommendationCategory
    input_params: tuple[str, ...]
    default_priority: RecommendationPriority


class RuleRegistry:
    """Реестр-синглтон, собирающий все декорированные функции правил."""

    def __init__(self) -> None:
        self._rules: dict[int, RuleSpec] = {}

    def register(self, spec: RuleSpec) -> None:
        if spec.number in self._rules:
            msg = f"Duplicate rule number: R{spec.number}"
            raise ValueError(msg)
        self._rules[spec.number] = spec

    def get_all(self) -> list[RuleSpec]:
        """Возвращает правила, отсортированные по (порядок группы, номер)."""
        return sorted(
            self._rules.values(),
            key=lambda r: (_GROUP_ORDER.get(r.group, 99), r.number),
        )

    def get_by_number(self, number: int) -> RuleSpec | None:
        return self._rules.get(number)

    @property
    def count(self) -> int:
        return len(self._rules)


registry = RuleRegistry()


def rule(
    number: int,
    group: RuleGroup,
    name: str,
    output_param: RecommendationCategory,
    input_params: tuple[str, ...],
    priority: RecommendationPriority,
) -> Callable[[RuleFunc], RuleFunc]:
    """Декоратор, регистрирующий функцию правила в глобальном реестре."""

    def decorator(func: RuleFunc) -> RuleFunc:
        spec = RuleSpec(
            number=number,
            group=group,
            name=name,
            func=func,
            output_param=output_param,
            input_params=input_params,
            default_priority=priority,
        )
        registry.register(spec)
        return func

    return decorator
