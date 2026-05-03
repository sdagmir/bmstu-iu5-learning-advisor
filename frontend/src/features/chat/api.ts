import { apiFetch } from '@/lib/api-client'
import type { ChatRequest, ChatResponse } from '@/types/api'

export const chatApi = {
  send: (body: ChatRequest) =>
    apiFetch<ChatResponse>('/chat/message', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
}
