"""Клиент для получения эмбеддингов текста.

Использует OpenRouter API (OpenAI-совместимый формат /embeddings).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings
from app.exceptions import UpstreamError

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Клиент эмбеддингов через OpenAI-совместимый API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        dimension: int | None = None,
    ) -> None:
        self._api_key = api_key or settings.llm_api_key
        self._base_url = base_url or settings.llm_base_url
        self._model = model or settings.embedding_model
        self._dimension = dimension or settings.embedding_dimension
        self._http = httpx.AsyncClient(
            base_url=self._base_url,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(30.0, connect=10.0),
        )

    async def embed(self, text: str) -> list[float]:
        """Получить вектор эмбеддинга для одного текста."""
        return (await self.embed_batch([text]))[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Получить эмбеддинги для списка текстов."""
        if not texts:
            return []

        payload: dict[str, Any] = {
            "model": self._model,
            "input": texts,
        }

        try:
            response = await self._http.post("/embeddings", json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("Embedding API ошибка: %s", exc.response.status_code)
            raise UpstreamError("Embedding", str(exc.response.status_code)) from exc
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise UpstreamError("Embedding", "Не удалось подключиться") from exc

        data = response.json()
        return [item["embedding"] for item in data["data"]]

    @property
    def dimension(self) -> int:
        return self._dimension

    async def close(self) -> None:
        await self._http.aclose()
