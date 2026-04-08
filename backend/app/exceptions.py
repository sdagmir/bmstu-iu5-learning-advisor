from __future__ import annotations


class AppError(Exception):
    """Базовый класс для всех доменных ошибок."""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    """Сущность не найдена. HTTP 404."""

    def __init__(self, entity: str, identifier: str) -> None:
        super().__init__(f"{entity} '{identifier}' not found")


class ForbiddenError(AppError):
    """Доступ запрещён. HTTP 403."""


class ValidationError(AppError):
    """Некорректный ввод. HTTP 422."""


class ConflictError(AppError):
    """Дубликат или конфликт состояния. HTTP 409."""


class UnauthorizedError(AppError):
    """Отсутствуют или некорректны учётные данные. HTTP 401."""


class UpstreamError(AppError):
    """Ошибка внешнего сервиса. HTTP 502."""

    def __init__(self, service: str, detail: str = "") -> None:
        super().__init__(f"{service} unavailable: {detail}")
