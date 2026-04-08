from __future__ import annotations

# Импорт всех модулей правил для срабатывания декораторов @rule.
# Порядок не важен — реестр сортирует по (группа, номер).
from app.expert.rules import (  # noqa: F401
    basic_universal,
    ck_programs,
    coursework,
    discipline_focus,
    strategy,
    technopark,
    warnings,
)
