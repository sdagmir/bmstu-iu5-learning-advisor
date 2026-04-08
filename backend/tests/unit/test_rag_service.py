"""Тесты RAG-модуля: BM25, чанкинг, гибридный поиск."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.bm25 import BM25Encoder
from app.rag.service import RAGService, split_into_chunks

# ── Тесты BM25 ──────────────────────────────────────────────────────────────


class TestBM25Encoder:
    def test_fit_builds_vocab(self) -> None:
        encoder = BM25Encoder()
        encoder.fit(["машинное обучение python", "базы данных sql"])
        assert encoder.vocab_size > 0
        assert encoder.vocab_size >= 5

    def test_encode_returns_sparse_vector(self) -> None:
        encoder = BM25Encoder()
        encoder.fit(["машинное обучение", "python программирование"])
        vec = encoder.encode("машинное обучение")
        assert len(vec.indices) > 0
        assert len(vec.indices) == len(vec.values)
        assert all(v > 0 for v in vec.values)

    def test_encode_empty_text(self) -> None:
        encoder = BM25Encoder()
        encoder.fit(["текст"])
        vec = encoder.encode("")
        assert vec.indices == []

    def test_encode_unknown_tokens(self) -> None:
        """Токены не из словаря игнорируются."""
        encoder = BM25Encoder()
        encoder.fit(["python java"])
        vec = encoder.encode("совершенно другие слова")
        assert vec.indices == []

    def test_encode_query_produces_values(self) -> None:
        encoder = BM25Encoder()
        encoder.fit(["машинное обучение python", "анализ данных sql"])
        vec = encoder.encode_query("машинное обучение")
        assert len(vec.indices) > 0

    def test_tokenizer_handles_cyrillic(self) -> None:
        tokens = BM25Encoder._tokenize("Машинное обучение и Data Science")
        assert "машинное" in tokens
        assert "обучение" in tokens
        assert "data" in tokens

    def test_tokenizer_filters_short(self) -> None:
        tokens = BM25Encoder._tokenize("я и ты по ООП")
        assert "я" not in tokens
        assert "ооп" in tokens

    def test_add_documents_incremental(self) -> None:
        """add_documents() накапливает корпус."""
        encoder = BM25Encoder()
        encoder.add_documents(["python машинное обучение"])
        count_first = encoder._doc_count

        encoder.add_documents(["sql базы данных"])
        assert encoder._doc_count == count_first + 1

    def test_fit_resets_state(self) -> None:
        """fit() сбрасывает и пересчитывает с нуля."""
        encoder = BM25Encoder()
        encoder.add_documents(["python java rust"] * 10)
        encoder.fit(["sql"])
        assert encoder._doc_count == 1


# ── Тесты чанкинга ──────────────────────────────────────────────────────────


class TestChunking:
    def test_empty_text(self) -> None:
        assert split_into_chunks("") == []

    def test_short_text(self) -> None:
        chunks = split_into_chunks("Короткий текст", chunk_size=100)
        assert len(chunks) == 1

    def test_splits_long_text(self) -> None:
        text = "Предложение номер один. " * 50
        chunks = split_into_chunks(text, chunk_size=200, overlap=20)
        assert len(chunks) > 1


# ── Тесты RAG-сервиса ───────────────────────────────────────────────────────


class TestRAGService:
    @pytest.mark.asyncio
    async def test_index_document(self) -> None:
        """Индексация: чанки → dense + sparse → Qdrant."""
        mock_embedder = AsyncMock()
        mock_embedder.dimension = 3
        mock_embedder.embed_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3]])

        mock_qdrant = MagicMock()
        mock_qdrant.ensure_collection = MagicMock()
        mock_qdrant.delete_by_source = MagicMock()
        mock_qdrant.upsert = MagicMock()

        mock_bm25 = MagicMock()
        mock_bm25.fit = MagicMock()
        mock_bm25.encode = MagicMock(return_value=MagicMock(indices=[0], values=[1.0]))

        service = RAGService(embedder=mock_embedder, qdrant=mock_qdrant, bm25=mock_bm25)
        count = await service.index_document("test.txt", "Текст документа.")

        assert count == 1
        mock_qdrant.upsert.assert_called_once()
        # BM25 пересчитывается через fit (rebuild)
        mock_bm25.fit.assert_called()

    @pytest.mark.asyncio
    async def test_search_hybrid(self) -> None:
        """Поиск: dense + sparse → hybrid_search."""
        mock_embedder = AsyncMock()
        mock_embedder.dimension = 3
        mock_embedder.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

        mock_qdrant = MagicMock()
        mock_qdrant.ensure_collection = MagicMock()
        mock_qdrant.hybrid_search = MagicMock(
            return_value=[
                {"content": "Результат", "source": "doc.txt", "score": 0.9, "chunk_index": 0},
            ]
        )

        mock_bm25 = MagicMock()
        mock_bm25.encode_query = MagicMock(return_value=MagicMock(indices=[0], values=[1.0]))

        service = RAGService(embedder=mock_embedder, qdrant=mock_qdrant, bm25=mock_bm25)
        results = await service.search("запрос")

        assert len(results) == 1
        assert results[0].content == "Результат"
        mock_qdrant.hybrid_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_empty_text(self) -> None:
        mock_embedder = AsyncMock()
        mock_embedder.dimension = 3
        mock_qdrant = MagicMock()
        mock_qdrant.ensure_collection = MagicMock()
        mock_qdrant.delete_by_source = MagicMock()

        service = RAGService(embedder=mock_embedder, qdrant=mock_qdrant)
        count = await service.index_document("empty.txt", "")
        assert count == 0

    def test_delete_rebuilds_bm25(self) -> None:
        """Удаление документа пересчитывает BM25."""
        mock_qdrant = MagicMock()
        mock_bm25 = MagicMock()
        mock_bm25.fit = MagicMock()
        mock_embedder = MagicMock()
        mock_embedder.dimension = 3

        service = RAGService(embedder=mock_embedder, qdrant=mock_qdrant, bm25=mock_bm25)
        # Имитируем что документ был проиндексирован ранее
        service._source_chunks["doc.txt"] = {"чанк 1", "чанк 2"}
        service._all_chunks = ["чанк 1", "чанк 2", "другой чанк"]

        service.delete_document("doc.txt")

        mock_qdrant.delete_by_source.assert_called_once_with("doc.txt")
        # BM25 пересчитан без удалённых чанков
        mock_bm25.fit.assert_called_once()
        assert len(service._all_chunks) == 1
        assert service._all_chunks[0] == "другой чанк"
