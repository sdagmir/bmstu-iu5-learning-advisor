"""Клиент Qdrant — гибридный поиск: dense + sparse (BM25) → RRF.

Коллекция хранит два типа векторов:
- "dense": семантические эмбеддинги от LLM
- "sparse": BM25 sparse-векторы для полнотекстового поиска

Поиск: prefetch dense + prefetch sparse → Reciprocal Rank Fusion.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING, Any

from app.config import settings
from app.exceptions import UpstreamError

if TYPE_CHECKING:
    from app.rag.bm25 import SparseVector

logger = logging.getLogger(__name__)

DENSE_VECTOR_NAME = "dense"
SPARSE_VECTOR_NAME = "sparse"


class QdrantService:
    """Обёртка Qdrant с гибридным поиском (dense + sparse → RRF)."""

    def __init__(self, url: str | None = None, collection: str | None = None) -> None:
        self._url = url or settings.qdrant_url
        self._collection = collection or settings.qdrant_collection
        self._client: Any = None

    def _get_client(self) -> Any:
        """Ленивая инициализация клиента Qdrant."""
        if self._client is None:
            try:
                from qdrant_client import QdrantClient

                self._client = QdrantClient(url=self._url)
                logger.info("Qdrant подключён: %s", self._url)
            except Exception as exc:
                raise UpstreamError("Qdrant", "Не удалось подключиться") from exc
        return self._client

    def ensure_collection(self, dense_dim: int) -> None:
        """Создать коллекцию с dense + sparse векторами если не существует."""
        from qdrant_client.models import (
            Distance,
            SparseVectorParams,
            VectorParams,
        )

        client = self._get_client()
        collections = [c.name for c in client.get_collections().collections]
        if self._collection not in collections:
            client.create_collection(
                collection_name=self._collection,
                vectors_config={
                    DENSE_VECTOR_NAME: VectorParams(size=dense_dim, distance=Distance.COSINE),
                },
                sparse_vectors_config={
                    SPARSE_VECTOR_NAME: SparseVectorParams(),
                },
            )
            logger.info(
                "Коллекция '%s' создана (dense=%d, sparse=BM25)",
                self._collection,
                dense_dim,
            )

    def upsert(
        self,
        doc_id: str,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        payload: dict[str, Any],
    ) -> None:
        """Добавить или обновить точку с dense + sparse векторами."""
        from qdrant_client.models import PointStruct
        from qdrant_client.models import SparseVector as QdrantSparseVector

        client = self._get_client()
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, doc_id))

        vectors: dict[str, Any] = {
            DENSE_VECTOR_NAME: dense_vector,
        }
        # Sparse вектор добавляем только если есть данные
        if sparse_vector.indices:
            vectors[SPARSE_VECTOR_NAME] = QdrantSparseVector(
                indices=sparse_vector.indices,
                values=sparse_vector.values,
            )

        client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=point_id, vector=vectors, payload=payload)],
        )

    def hybrid_search(
        self,
        dense_vector: list[float],
        sparse_vector: SparseVector,
        *,
        top_k: int = 5,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Гибридный поиск: dense + sparse → RRF.

        Использует Qdrant Query API: prefetch dense и sparse, потом RRF fusion.
        """
        from qdrant_client.models import Fusion, Prefetch
        from qdrant_client.models import SparseVector as QdrantSparseVector

        client = self._get_client()

        prefetches = [
            Prefetch(
                query=dense_vector,
                using=DENSE_VECTOR_NAME,
                limit=top_k * 2,
            ),
        ]

        # Sparse prefetch только если есть токены
        if sparse_vector.indices:
            prefetches.append(
                Prefetch(
                    query=QdrantSparseVector(
                        indices=sparse_vector.indices,
                        values=sparse_vector.values,
                    ),
                    using=SPARSE_VECTOR_NAME,
                    limit=top_k * 2,
                ),
            )

        results = client.query_points(
            collection_name=self._collection,
            prefetch=prefetches,
            query=Fusion.RRF,
            limit=top_k,
        )

        return [
            {
                "content": hit.payload.get("content", ""),
                "source": hit.payload.get("source", ""),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "score": hit.score,
            }
            for hit in results.points
            if hit.score >= score_threshold
        ]

    def delete_by_source(self, source: str) -> None:
        """Удалить все точки с указанным source."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        client = self._get_client()
        client.delete(
            collection_name=self._collection,
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=source))]
            ),
        )

    def count(self) -> int:
        """Количество точек в коллекции."""
        client = self._get_client()
        return client.count(collection_name=self._collection).count

    def scroll_all_content(self, batch_size: int = 100) -> dict[str, list[str]]:
        """Получить все чанки из коллекции, сгруппированные по source.

        Используется для восстановления BM25 корпуса при старте.
        """
        client = self._get_client()
        source_chunks: dict[str, list[str]] = {}
        offset = None

        while True:
            results, offset = client.scroll(
                collection_name=self._collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            if not results:
                break
            for point in results:
                source = point.payload.get("source", "unknown")
                content = point.payload.get("content", "")
                if content:
                    source_chunks.setdefault(source, []).append(content)
            if offset is None:
                break

        return source_chunks

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
