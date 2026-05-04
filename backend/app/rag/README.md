# rag — Семантический поиск по базе знаний

## Что делает

Гибридный поиск: dense (семантика) + sparse (BM25) → RRF fusion.
Обогащает ответы ЭС контекстом из документов (курсы ЦК, Технопарк, вакансии).

## Архитектура

```
Индексация:
  документ → чанки (500 симв., overlap 50) → dense embedding + BM25 sparse → Qdrant

Поиск:
  запрос → dense + sparse → Qdrant prefetch → Fusion.RRF → топ-K чанков
```

## Гибридный поиск

```
┌──────────────┐   prefetch   ┌──────────┐
│ Dense vector  ├─────────────►│          │
│ (семантика)   │              │  Qdrant  │──► RRF fusion ──► результаты
│ BM25 sparse   ├─────────────►│          │
│ (ключевые)    │   prefetch   └──────────┘
└──────────────┘
```

- **Dense**: text-embedding-3-small (1536 dims), семантическое сходство
- **Sparse (BM25)**: Okapi BM25 (k1=1.5, b=0.75), кириллица + латиница
- **RRF**: Qdrant native `Fusion.RRF`, объединяет ранги обоих поисков

## Консистентность

- BM25 корпус полностью пересчитывается при каждой мутации (индексация/удаление)
- При перезапуске BM25 восстанавливается из Qdrant (`restore_bm25_from_qdrant` в lifespan)
- Embedding batch size = 64 (защита от rate limit)

## API

| Метод | Путь | Роль | Описание |
|-------|------|------|----------|
| GET | `/rag/documents` | admin | Список источников с агрегатами (chunks_count, indexed_at) |
| POST | `/rag/documents` | admin | Загрузка документа → чанки + эмбеддинги |
| DELETE | `/rag/documents/{source:path}` | admin | Удаление документа и его чанков |
| POST | `/rag/search` | user | Гибридный поиск (top_k=5) |
| GET | `/rag/stats` | admin | Статистика (кол-во чанков) |

## Файлы

| Файл | Описание |
|------|----------|
| `bm25.py` | BM25Encoder: fit/add_documents/encode, sparse vectors, токенизация |
| `embedder.py` | OpenAI-совместимый /embeddings клиент (batch=64) |
| `qdrant_client.py` | Named vectors (dense + sparse), hybrid_search, Fusion.RRF |
| `service.py` | Чанкинг, индексация, поиск, BM25 rebuild, restore at startup |
| `schemas.py` | DocumentChunk, DocumentUpload, SearchRequest, RAGStats |
| `router.py` | 4 эндпоинта |
