import { apiFetch } from '@/lib/api-client'
import type { ChatRequest, ChatResponse } from '@/types/api'

/**
 * Debug-вариант LLM-чата. Возвращает `debug` со списком сработавших правил,
 * RAG-чанков, tool-calls и изменений профиля — то, что в Phase 10 заменяет
 * полноценный «журнал трейсов» (его эндпоинта нет на бэке).
 */
export const tracesApi = {
  sendDebug: (body: ChatRequest) =>
    apiFetch<ChatResponse>('/chat/message/debug', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
