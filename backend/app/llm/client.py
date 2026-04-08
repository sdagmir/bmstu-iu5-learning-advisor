"""OpenRouter API клиент (OpenAI-совместимый).

Поддержка: нестриминговые запросы, function calling, retry с backoff.
Обработка всех типов ошибок OpenRouter: 401, 402, 408, 429, 5xx.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import httpx

from app.config import settings
from app.exceptions import UpstreamError

logger = logging.getLogger(__name__)

# Retry-конфигурация
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.0  # секунды
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class OpenRouterClient:
    """HTTP-клиент для OpenRouter API.

    Автоматический retry для 429 (rate limit) и 5xx ошибок.
    Модель переключается через конструктор или settings.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._api_key = api_key or settings.llm_api_key
        self._base_url = base_url or settings.llm_base_url
        self._model = model or settings.llm_model
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://rs-ito.bmstu.ru",
                "X-Title": "RS ITO - BMSTU Diploma",
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    @property
    def model(self) -> str:
        """Текущая модель."""
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        """Переключение модели без пересоздания клиента."""
        self._model = value

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """Нестриминговый запрос к LLM с retry."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature if temperature is not None else settings.llm_temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        last_error: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._http.post("/chat/completions", json=payload)
                response.raise_for_status()
                data = response.json()
                self._validate_response(data)
                return data

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                last_error = exc
                body = self._safe_parse_error(exc.response)

                if status == 401:
                    raise UpstreamError("OpenRouter", "Неверный API-ключ") from exc
                if status == 402:
                    raise UpstreamError("OpenRouter", "Недостаточно кредитов") from exc
                if status == 403:
                    raise UpstreamError(
                        "OpenRouter", f"Запрос заблокирован модерацией: {body}"
                    ) from exc

                if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                    wait = self._get_retry_delay(exc.response, attempt)
                    logger.warning(
                        "LLM API %d, попытка %d/%d, ожидание %.1f сек",
                        status,
                        attempt + 1,
                        MAX_RETRIES,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                logger.error("LLM API ошибка: %d %s", status, body)
                raise UpstreamError("OpenRouter", f"HTTP {status}: {body}") from exc

            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "LLM API таймаут, попытка %d/%d, ожидание %.1f сек",
                        attempt + 1,
                        MAX_RETRIES,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise UpstreamError("OpenRouter", "Таймаут запроса") from exc

            except httpx.ConnectError as exc:
                raise UpstreamError("OpenRouter", "Не удалось подключиться") from exc

        raise UpstreamError("OpenRouter", "Исчерпаны попытки") from last_error

    async def close(self) -> None:
        """Закрытие HTTP-клиента."""
        await self._http.aclose()

    @staticmethod
    def extract_content(response: dict[str, Any]) -> str:
        """Извлечь текст ответа из LLM response."""
        try:
            return response["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError):
            return ""

    @staticmethod
    def extract_tool_calls(response: dict[str, Any]) -> list[dict[str, Any]]:
        """Извлечь tool_calls из LLM response."""
        try:
            message = response["choices"][0]["message"]
            return message.get("tool_calls") or []
        except (KeyError, IndexError):
            return []

    @staticmethod
    def parse_tool_arguments(tool_call: dict[str, Any]) -> dict[str, Any]:
        """Распарсить аргументы tool_call. Возвращает {} при ошибке парсинга."""
        try:
            args_str = tool_call["function"]["arguments"]
            return json.loads(args_str)
        except (KeyError, json.JSONDecodeError) as exc:
            logger.warning("Ошибка парсинга аргументов tool_call: %s", exc)
            return {}

    @staticmethod
    def _validate_response(data: dict[str, Any]) -> None:
        """Проверка структуры ответа. Кидает UpstreamError если ответ невалидный."""
        if "error" in data:
            err = data["error"]
            msg = err.get("message", str(err))
            raise UpstreamError("OpenRouter", msg)
        if not data.get("choices"):
            raise UpstreamError("OpenRouter", "Пустой ответ (нет choices)")

    @staticmethod
    def _get_retry_delay(response: httpx.Response, attempt: int) -> float:
        """Вычислить задержку перед retry. Учитывает Retry-After от сервера."""
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return RETRY_BACKOFF_BASE * (2**attempt)

    @staticmethod
    def _safe_parse_error(response: httpx.Response) -> str:
        """Безопасно извлечь сообщение ошибки из ответа."""
        try:
            data = response.json()
            if "error" in data:
                return data["error"].get("message", str(data["error"]))
            return response.text[:200]
        except Exception:
            return response.text[:200]
