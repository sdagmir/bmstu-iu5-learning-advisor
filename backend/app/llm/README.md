# llm — LLM-оркестратор

## Что делает

Переводчик между студентом и формальными компонентами (ЭС + RAG).
**НЕ принимает решений** о рекомендациях — только оркестрирует вызовы и формирует ответ.

## Поток

```
Сообщение студента
        ↓
  ProfileBuilder → StudentProfile (X1-X12 из БД автоматически)
        ↓
  LLM (OpenRouter) + system prompt + профиль + история
        ↓
  Function calling (до 3 итераций):
    get_recommendations()        → ЭС → рекомендации
    recalculate_with_changes()   → ЭС с изменённым профилем
    search_knowledge()           → RAG → чанки из базы знаний
        ↓
  LLM формирует ответ на русском
```

## Function calling

| Функция | Когда | Параметры |
|---------|-------|-----------|
| `get_recommendations` | Первый запрос о траектории | нет |
| `recalculate_with_changes` | «А если сменить цель на ML?» | career_goal, technopark_status, workload_pref |
| `search_knowledge` | «Расскажи про курс...» | query (текст) |

## Ограничения

- Через диалог можно менять: цель, ТП, нагрузку
- **Нельзя** через диалог: семестр, оценки, пройденные ЦК (только форма)
- Max 3 итерации function calling за один запрос
- Retry с exponential backoff для 429/5xx (max 3 попытки)
- Graceful fallback при недоступности RAG

## API

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/chat/message` | Чат студента |
| POST | `/chat/message/debug` | Debug-чат админа (rules_fired, rag_chunks, tool_calls) |

## Файлы

| Файл | Описание |
|------|----------|
| `client.py` | OpenRouter httpx клиент, retry, обработка 401/402/403/429 |
| `prompts.py` | Системный промпт, TOOL_DEFINITIONS, форматирование профиля |
| `service.py` | ChatService — оркестрация LLM + ЭС + RAG |
| `schemas.py` | ChatRequest, ChatResponse, DebugInfo |
| `router.py` | 2 эндпоинта |
