"""RAG-сервис: гибридный поиск (dense + BM25 sparse → RRF).

Поток индексации:
1. Админ загружает документ → чанкинг
2. Dense-эмбеддинг (OpenRouter) + BM25 sparse-вектор
3. Оба вектора сохраняются в Qdrant
4. BM25 корпус пересчитывается по актуальным данным

Поток поиска:
1. Эмбеддинг запроса (dense) + BM25 запроса (sparse)
2. Qdrant: prefetch dense + prefetch sparse → RRF fusion
3. Возврат топ-K чанков
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from app.rag.bm25 import BM25Encoder
from app.rag.embedder import EmbeddingClient
from app.rag.qdrant_client import QdrantService
from app.rag.schemas import DocumentChunk, RAGDocumentSummary

logger = logging.getLogger(__name__)

# Параметры чанкинга. 1000 символов даёт лучше семантический контекст для
# text-embedding-3-small (короткие ~500-чанки терялись по смыслу). Overlap
# 10% — достаточно чтобы не разрезать важные мысли пополам.
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100

# Батч для эмбеддингов (лимит API)
EMBEDDING_BATCH_SIZE = 64

# TTL кэша списка документов (sec) — балансирует частоту scroll-обхода Qdrant
# и свежесть после upload/delete (мутации сами инвалидируют кэш)
DOCUMENTS_CACHE_TTL = 60.0

# Фильтр на возврат поиска: сбрасываем чанки со score ниже половины топа.
# RRF score не сравним с косинусом (он маленький, ~0.03 для top-1), поэтому
# абсолютный порог не работает — используем относительный к лучшему чанку.
# Защищает LLM от шума, когда в корпусе нет ничего релевантного запросу.
SEARCH_RELATIVE_THRESHOLD = 0.5


# Сепараторы в порядке приоритета: сначала границы абзацев, потом
# предложений, потом слов. Разрыв абзаца (\n\n) — лучшая семантическая
# граница и должна предпочитаться даже если предложение могло бы влезть.
_CHUNK_SEPARATORS = ("\n\n", ".\n", ". ", "\n", " ")


def split_into_chunks(
    text: str,
    *,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Разбить текст на чанки с перекрытием по границам абзацев/предложений.

    Граница чанка — поздний сепаратор во второй половине окна chunk_size,
    приоритет от абзаца к слову. Overlap тоже привязан к ближайшей границе
    в `[end-overlap, end]` — иначе чанк начинается с обрывка слова и
    выглядит как мусор в UI и в LLM-промпте.
    """
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        if end < text_len:
            # Поздняя граница во второй половине окна, приоритет paragraph > sentence
            min_end = start + chunk_size // 2
            for sep in _CHUNK_SEPARATORS:
                pos = text.rfind(sep, min_end, end)
                if pos != -1:
                    end = pos + len(sep)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_len:
            break

        # Старт следующего чанка: ~overlap символов назад, но привязан
        # к границе. Если в окне [end-overlap, end] нет ни одной границы —
        # стартуем с end (без overlap), не разрезая слово.
        ideal = max(start + 1, end - overlap)
        next_start = end
        for sep in _CHUNK_SEPARATORS:
            pos = text.find(sep, ideal, end)
            if pos != -1:
                next_start = pos + len(sep)
                break

        # Защита от зацикливания: следующий старт должен двигаться вперёд
        if next_start <= start:
            next_start = end
        start = next_start

    return chunks


class RAGService:
    """Сервис загрузки и гибридного поиска по базе знаний.

    BM25 корпус полностью пересчитывается при каждом изменении данных
    (индексация/удаление). Это гарантирует консистентность IDF-статистик.
    """

    def __init__(
        self,
        embedder: EmbeddingClient | None = None,
        qdrant: QdrantService | None = None,
        bm25: BM25Encoder | None = None,
    ) -> None:
        self._embedder = embedder or EmbeddingClient()
        self._qdrant = qdrant or QdrantService()
        self._bm25 = bm25 or BM25Encoder()
        self._initialized = False
        # Кэш всех чанков для BM25 пересчёта
        self._all_chunks: list[str] = []
        # TTL-кэш агрегатов по source для GET /rag/documents
        self._docs_cache: list[dict[str, Any]] | None = None
        self._docs_cache_at: float = 0.0

    def _ensure_collection(self) -> None:
        """Создать коллекцию при первом использовании."""
        if not self._initialized:
            self._qdrant.ensure_collection(self._embedder.dimension)
            self._initialized = True

    def _rebuild_bm25(self) -> None:
        """Пересчитать BM25 по актуальному корпусу."""
        self._bm25.fit(self._all_chunks)

    def restore_bm25_from_qdrant(self) -> int:
        """Восстановить BM25 корпус из Qdrant при старте приложения.

        Загружает все чанки из коллекции и пересчитывает BM25 статистики.
        Возвращает количество загруженных чанков.
        """
        try:
            source_chunks = self._qdrant.scroll_all_content()
        except Exception:
            logger.warning("Qdrant недоступен, BM25 корпус пустой")
            return 0

        self._all_chunks = []
        self._source_chunks_map = {}
        for source, chunks in source_chunks.items():
            self._all_chunks.extend(chunks)
            self._source_chunks_map[source] = set(chunks)

        self._rebuild_bm25()
        total = len(self._all_chunks)
        if total > 0:
            logger.info(
                "BM25 восстановлен: %d чанков из %d документов",
                total,
                len(source_chunks),
            )
        return total

    async def index_document(self, source: str, text: str) -> int:
        """Загрузить документ: чанкинг → dense + sparse → Qdrant.

        Идемпотентный: при повторной загрузке старые чанки удаляются.
        BM25 полностью пересчитывается для консистентности.

        Возвращает количество сохранённых чанков.
        """
        self._ensure_collection()

        # Удаляем старые чанки из Qdrant и кэша
        self._qdrant.delete_by_source(source)
        old = self._source_chunks.pop(source, set())
        self._all_chunks = [c for c in self._all_chunks if c not in old]

        chunks = split_into_chunks(text)
        if not chunks:
            self._rebuild_bm25()
            return 0

        # Сохраняем чанки в кэш и пересчитываем BM25
        self._all_chunks.extend(chunks)
        self._source_chunks[source] = set(chunks)
        self._rebuild_bm25()

        # Dense-эмбеддинги батчами
        dense_vectors: list[list[float]] = []
        for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
            batch = chunks[i : i + EMBEDDING_BATCH_SIZE]
            dense_vectors.extend(await self._embedder.embed_batch(batch))

        # Sparse BM25 векторы
        sparse_vectors = [self._bm25.encode(chunk) for chunk in chunks]

        indexed_at = datetime.now(UTC).isoformat()

        # Сохраняем в Qdrant
        for i, (chunk, dense, sparse) in enumerate(
            zip(chunks, dense_vectors, sparse_vectors, strict=True)
        ):
            doc_id = f"{source}::chunk_{i}"
            self._qdrant.upsert(
                doc_id=doc_id,
                dense_vector=dense,
                sparse_vector=sparse,
                payload={
                    "content": chunk,
                    "source": source,
                    "chunk_index": i,
                    "indexed_at": indexed_at,
                },
            )

        self._invalidate_docs_cache()
        logger.info("Проиндексировано: %s (%d чанков)", source, len(chunks))
        return len(chunks)

    async def search(self, query: str, *, top_k: int = 5) -> list[DocumentChunk]:
        """Гибридный поиск: dense + BM25 sparse → RRF.

        Relative score filter: оставляем только чанки со score ≥ 50% от
        лучшего. Когда в корпусе нет релевантного контента, RRF всё равно
        вернёт top_k — но с большим разрывом между первым и остальными,
        и фильтр сбросит хвост шума.
        """
        self._ensure_collection()

        dense_vector = await self._embedder.embed(query)
        sparse_vector = self._bm25.encode_query(query)

        results = self._qdrant.hybrid_search(
            dense_vector=dense_vector,
            sparse_vector=sparse_vector,
            top_k=top_k,
        )

        if not results:
            return []

        top_score = results[0]["score"]
        threshold = top_score * SEARCH_RELATIVE_THRESHOLD
        filtered = [r for r in results if r["score"] >= threshold]

        return [
            DocumentChunk(
                content=r["content"],
                source=r["source"],
                score=r["score"],
            )
            for r in filtered
        ]

    def delete_document(self, source: str) -> None:
        """Удалить документ из базы знаний и пересчитать BM25."""
        self._qdrant.delete_by_source(source)

        # Удаляем чанки из кэша и пересчитываем BM25
        old_chunks = self._source_chunks.pop(source, set())
        self._all_chunks = [c for c in self._all_chunks if c not in old_chunks]
        self._rebuild_bm25()
        self._invalidate_docs_cache()

        logger.info("Удалён документ: %s", source)

    def document_count(self) -> int:
        """Количество чанков в базе знаний."""
        return self._qdrant.count()

    def list_documents(self, *, offset: int = 0, limit: int = 50) -> list[RAGDocumentSummary]:
        """Список уникальных source с агрегатами (chunks_count, indexed_at).

        Пагинация — по списку источников (не по чанкам), отсортированных
        алфавитно для стабильности. Результат кэшируется на 60 сек, чтобы
        админский UI не ронял Qdrant scroll'ами на каждом open-page.
        Мутации (`index_document` / `delete_document`) инвалидируют кэш
        локально через `_invalidate_docs_cache()`.
        """
        self._ensure_collection()

        now = time.monotonic()
        if (
            self._docs_cache is not None
            and now - self._docs_cache_at < DOCUMENTS_CACHE_TTL
        ):
            rows = self._docs_cache
        else:
            rows = self._qdrant.aggregate_sources()
            self._docs_cache = rows
            self._docs_cache_at = now

        page = rows[offset : offset + limit]
        return [
            RAGDocumentSummary(
                source=row["source"],
                chunks_count=row["chunks_count"],
                indexed_at=(
                    datetime.fromisoformat(row["indexed_at"]) if row.get("indexed_at") else None
                ),
            )
            for row in page
        ]

    def _invalidate_docs_cache(self) -> None:
        """Сбросить TTL-кэш `list_documents` (после upload/delete)."""
        self._docs_cache = None
        self._docs_cache_at = 0.0

    async def close(self) -> None:
        await self._embedder.close()
        self._qdrant.close()

    @property
    def _source_chunks(self) -> dict[str, set[str]]:
        """Ленивая инициализация маппинга source → множество чанков."""
        if not hasattr(self, "_source_chunks_map"):
            self._source_chunks_map: dict[str, set[str]] = {}
        return self._source_chunks_map


rag_service = RAGService()
