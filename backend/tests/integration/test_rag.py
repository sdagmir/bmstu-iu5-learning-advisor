"""Integration-тесты модуля RAG: загрузка/удаление документов, поиск, статистика.

Используются `fake_embedder` (детерминированные векторы по hash) и реальный Qdrant
из docker-compose. Перед каждым тестом коллекция Qdrant очищается через delete_document
для всех источников, оставленных предыдущими тестами.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.rag.service import rag_service

from tests.integration._fakes import FakeEmbeddingClient

pytestmark = pytest.mark.asyncio(loop_scope="session")


@pytest.fixture(autouse=True)
def _clean_rag(fake_embedder: FakeEmbeddingClient) -> None:
    """Перед каждым тестом — очистить Qdrant и in-memory кэш RAG-сервиса.

    fake_embedder подставляется автоматически на время теста (см. conftest).
    """
    # Удаляем все известные сервису источники
    sources = list(rag_service._source_chunks.keys())
    for source in sources:
        try:
            rag_service.delete_document(source)
        except Exception:
            pass
    # На всякий случай дочищаем коллекцию полностью через scroll
    try:
        all_sources = rag_service._qdrant.scroll_all_content()
        for source in all_sources:
            rag_service._qdrant.delete_by_source(source)
    except Exception:
        pass
    # Сброс in-memory кэша
    rag_service._all_chunks = []
    if hasattr(rag_service, "_source_chunks_map"):
        rag_service._source_chunks_map = {}
    rag_service._bm25.fit([])


class TestUploadDocument:
    async def test_upload_single_document(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """Загрузка короткого документа возвращает 201 и chunks_count=1."""
        response = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "test1.txt", "text": "Короткий документ для проверки."},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["source"] == "test1.txt"
        assert data["chunks_count"] == 1

    async def test_upload_forbidden_for_student(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Студент не может загружать документы — 403."""
        response = await client.post(
            "/api/v1/rag/documents",
            headers=student_auth,
            json={"source": "x.txt", "text": "abc"},
        )
        assert response.status_code == 403

    async def test_long_text_creates_multiple_chunks(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """Длинный текст (>500 симв) разбивается на несколько чанков."""
        # Каждое предложение около 100 символов; 12 предложений — около 1200 знаков
        sentence = (
            "Это длинное тестовое предложение для проверки чанкинга в RAG модуле системы. "
        )
        long_text = sentence * 12
        response = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "long.txt", "text": long_text},
        )
        assert response.status_code == 201
        assert response.json()["chunks_count"] >= 2

    async def test_reupload_replaces_old_chunks(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """Повторная загрузка того же source удаляет старые чанки."""
        # Первая загрузка — длинный текст (несколько чанков)
        long_text = "Старая версия документа. " * 30
        first = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "doc.txt", "text": long_text},
        )
        old_chunks = first.json()["chunks_count"]
        assert old_chunks >= 2

        # Повторная загрузка — короткий текст (1 чанк)
        second = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "doc.txt", "text": "Новая короткая версия."},
        )
        assert second.status_code == 201
        assert second.json()["chunks_count"] == 1

        # Проверяем что в кэше осталось ровно chunks от новой версии
        assert len(rag_service._source_chunks["doc.txt"]) == 1

        # И общее число чанков по статистике соответствует
        stats = await client.get("/api/v1/rag/stats", headers=admin_auth)
        assert stats.json()["total_chunks"] == 1


class TestSearch:
    async def test_search_empty_collection_returns_empty(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Поиск по пустой коллекции — пустой массив."""
        response = await client.post(
            "/api/v1/rag/search",
            headers=student_auth,
            json={"query": "что-нибудь", "top_k": 5},
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_search_returns_chunk_after_upload(
        self,
        client: AsyncClient,
        admin_auth: dict[str, str],
        student_auth: dict[str, str],
    ) -> None:
        """После загрузки документа поиск находит хотя бы один чанк."""
        await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "ml.txt", "text": "Машинное обучение и нейросети."},
        )
        response = await client.post(
            "/api/v1/rag/search",
            headers=student_auth,
            json={"query": "машинное обучение", "top_k": 5},
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 1
        assert all("content" in r and "source" in r and "score" in r for r in results)

    async def test_search_top_k_limits_results(
        self, client: AsyncClient, admin_auth: dict[str, str], student_auth: dict[str, str]
    ) -> None:
        """top_k ограничивает количество результатов."""
        # Загружаем 10 коротких документов
        for i in range(10):
            await client.post(
                "/api/v1/rag/documents",
                headers=admin_auth,
                json={
                    "source": f"doc_{i}.txt",
                    "text": f"Документ номер {i} с уникальным содержимым.",
                },
            )
        response = await client.post(
            "/api/v1/rag/search",
            headers=student_auth,
            json={"query": "документ", "top_k": 3},
        )
        assert response.status_code == 200
        assert len(response.json()) <= 3


class TestDeleteDocument:
    async def test_delete_returns_204_and_removes_chunks(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """DELETE возвращает 204, чанки исчезают из коллекции."""
        await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "todelete.txt", "text": "Будет удалён."},
        )
        stats_before = await client.get("/api/v1/rag/stats", headers=admin_auth)
        assert stats_before.json()["total_chunks"] >= 1

        response = await client.delete(
            "/api/v1/rag/documents/todelete.txt", headers=admin_auth
        )
        assert response.status_code == 204

        stats_after = await client.get("/api/v1/rag/stats", headers=admin_auth)
        assert stats_after.json()["total_chunks"] == 0

    async def test_delete_forbidden_for_student(
        self, client: AsyncClient, admin_auth: dict[str, str], student_auth: dict[str, str]
    ) -> None:
        """Студент не может удалять документы — 403."""
        await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "victim.txt", "text": "abc"},
        )
        response = await client.delete(
            "/api/v1/rag/documents/victim.txt", headers=student_auth
        )
        assert response.status_code == 403


class TestStats:
    async def test_stats_zero_for_empty_collection(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """На пустой коллекции total_chunks=0."""
        response = await client.get("/api/v1/rag/stats", headers=admin_auth)
        assert response.status_code == 200
        assert response.json()["total_chunks"] == 0

    async def test_stats_after_upload(
        self, client: AsyncClient, admin_auth: dict[str, str]
    ) -> None:
        """После загрузки stats отражает корректное количество чанков."""
        long_text = "Тестовое предложение для подсчёта чанков. " * 25
        upload = await client.post(
            "/api/v1/rag/documents",
            headers=admin_auth,
            json={"source": "stats.txt", "text": long_text},
        )
        chunks_count = upload.json()["chunks_count"]

        response = await client.get("/api/v1/rag/stats", headers=admin_auth)
        assert response.status_code == 200
        assert response.json()["total_chunks"] == chunks_count

    async def test_stats_forbidden_for_student(
        self, client: AsyncClient, student_auth: dict[str, str]
    ) -> None:
        """Студент не имеет доступа к stats — 403."""
        response = await client.get("/api/v1/rag/stats", headers=student_auth)
        assert response.status_code == 403
