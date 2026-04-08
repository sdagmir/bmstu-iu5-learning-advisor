# llm — LLM-оркестратор

## Что делает
Переводчик между студентом и формальными компонентами (ЭС + RAG).
НЕ принимает решений о рекомендациях — только оркестрирует.

## Поток
```
Сообщение студента
        ↓
  LLM (OpenRouter) + system prompt + профиль + история
        ↓
  Function calling:
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
| `recalculate_with_changes` | «А если сменить цель...» | career_goal, technopark_status, workload_pref (enum) |
| `search_knowledge` | «Расскажи про курс...» | query (текст) |

## Защита
- Через диалог можно менять: цель, ТП, нагрузку
- Нельзя: семестр, курсы, оценки (только форма)
- Max 3 итерации function calling
- Retry с backoff для 429/5xx
- Graceful fallback при недоступности RAG

## API
| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/chat/message` | Чат студента |
| POST | `/chat/message/debug` | Debug-чат админа (trace, tool_calls) |

## Файлы
- `client.py` — OpenRouter httpx клиент, retry, обработка ошибок
- `prompts.py` — системный промпт, TOOL_DEFINITIONS, форматирование
- `service.py` — ChatService, оркестрация
- `router.py` — эндпоинты
- `schemas.py` — ChatRequest, ChatResponse, DebugInfo
