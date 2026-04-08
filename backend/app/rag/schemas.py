from __future__ import annotations

from pydantic import BaseModel


class DocumentChunk(BaseModel):
    """Фрагмент документа, полученный из векторного поиска."""

    content: str
    source: str
    score: float
