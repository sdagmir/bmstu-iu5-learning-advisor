import { useCallback, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { chatApi } from './api'
import type { ChatHistoryItem } from '@/types/api'

export type ChatRole = 'user' | 'assistant' | 'error'

export interface ChatMessage {
  id: string
  role: ChatRole
  content: string
}

const newId = (): string =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `${Date.now()}-${Math.random().toString(36).slice(2)}`

/**
 * Хранение и отправка сообщений чата.
 * История — на клиенте (in-memory), сервер stateless. На каждом send шлём
 * всю историю кроме error-сообщений (это локальные UI-маркеры, не реплики).
 *
 * После каждого ответа ассистента инвалидируем кеш рекомендаций — LLM мог
 * через function-calling изменить профиль (`recalculate_with_changes`).
 */
export function useChatSession() {
  const queryClient = useQueryClient()
  const [messages, setMessages] = useState<ChatMessage[]>([])

  const sendMut = useMutation({
    mutationFn: chatApi.send,
    onSuccess: (res) => {
      setMessages((prev) => [
        ...prev,
        { id: newId(), role: 'assistant', content: res.reply },
      ])
      // LLM мог менять профиль через recalculate_with_changes — обновим всё связанное.
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] })
      queryClient.invalidateQueries({ queryKey: ['expert', 'my-recommendations'] })
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: newId(),
          role: 'error',
          content: 'Не удалось получить ответ. Проверь соединение и попробуй ещё раз.',
        },
      ])
    },
  })

  const send = useCallback(
    (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return

      const userMessage: ChatMessage = { id: newId(), role: 'user', content: trimmed }
      setMessages((prev) => [...prev, userMessage])

      // История для бэка — без error-маркеров и без только что добавленного user-сообщения
      // (бэк ждёт его в `message`, не в `history`).
      const history: ChatHistoryItem[] = messages
        .filter((m) => m.role !== 'error')
        .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))

      sendMut.mutate({ message: trimmed, history })
    },
    [messages, sendMut],
  )

  const retry = useCallback(() => {
    // Найти последнее user-сообщение и переотправить
    const lastUser = [...messages].reverse().find((m) => m.role === 'user')
    if (!lastUser) return
    // Удалить error-маркеры в конце
    setMessages((prev) => {
      const tail = [...prev]
      while (tail.length > 0 && tail.at(-1)?.role === 'error') tail.pop()
      return tail
    })
    // Переотправляем — но useState async, поэтому просто вызываем sendMut с историей
    // ДО того как user-сообщение было вставлено (чтобы не дублировать)
    const beforeLastUser = messages.slice(
      0,
      messages.findLastIndex((m) => m.role === 'user'),
    )
    const history: ChatHistoryItem[] = beforeLastUser
      .filter((m) => m.role !== 'error')
      .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }))
    sendMut.mutate({ message: lastUser.content, history })
  }, [messages, sendMut])

  const clear = useCallback(() => setMessages([]), [])

  return {
    messages,
    send,
    retry,
    clear,
    isPending: sendMut.isPending,
    canRetry: messages.at(-1)?.role === 'error',
  }
}
