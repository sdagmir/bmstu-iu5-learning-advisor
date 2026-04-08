from __future__ import annotations

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    """Фрагмент документа из векторного поиска."""

    content: str
    source: str
    score: float


class DocumentUpload(BaseModel):
    """Запрос на загрузку документа в RAG."""

    source: str
    text: str


class DocumentUploadResult(BaseModel):
    """Результат загрузки документа."""

    source: str
    chunks_count: int


class SearchRequest(BaseModel):
    """Запрос на семантический поиск."""

    query: str
    top_k: int = 5


class RAGStats(BaseModel):
    """Статистика RAG-базы."""

    total_chunks: int
