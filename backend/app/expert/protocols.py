from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.expert.schemas import Recommendation, StudentProfile


class ExpertEngine(Protocol):
    """Интерфейс экспертной системы.

    Реализации:
    - PythonRuleEngine (app.expert.engine) — 52 правила на Python
    - KesmiAdapter (будущее) — КЭСМИ Wi!Mi Разуматор через HTTP
    """

    def evaluate(self, profile: StudentProfile) -> list[Recommendation]:
        """Вычисление всех правил по профилю студента.

        Чистая функция: один вход → один выход. Без побочных эффектов.
        """
        ...
