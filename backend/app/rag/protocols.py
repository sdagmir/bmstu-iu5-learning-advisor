from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.rag.schemas import DocumentChunk


class VectorSearch(Protocol):
    """Интерфейс векторного поиска.

    Реализации:
    - QdrantSearch (app.rag.qdrant_client) — Qdrant
    """

    async def search(self, query: str, *, top_k: int = 5) -> list[DocumentChunk]:
        """Семантический поиск по базе знаний."""
        ...


class Embedder(Protocol):
    """Интерфейс модели эмбеддингов."""

    async def embed(self, text: str) -> list[float]:
        """Преобразование текста в векторное представление."""
        ...
