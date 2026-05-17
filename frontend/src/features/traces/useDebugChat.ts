import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { tracesApi } from './api'
import { usePersistentState } from '@/hooks/usePersistentState'
import type { ChatHistoryItem, ChatResponse } from '@/types/api'

/**
 * Хук-обёртка debug-чата для trace-инспектора. История + lastResponse
 * persist'ятся в `sessionStorage` — admin может листнуть на правила и
 * вернуться, debug-панель и история останутся.
 */
export function useDebugChat() {
  const [history, setHistory] = usePersistentState<ChatHistoryItem[]>(
    'admin.debug-chat.history',
    [],
  )
  const [lastResponse, setLastResponse] = usePersistentState<ChatResponse | null>(
    'admin.debug-chat.last-response',
    null,
  )

  const mut = useMutation({
    mutationKey: ['admin', 'traces', 'debug-chat'],
    mutationFn: ({ message, history: h }: { message: string; history: ChatHistoryItem[] }) =>
      tracesApi.sendDebug({ message, history: h }),
    onSuccess: (resp) => {
      setLastResponse(resp)
      setHistory((prev) => [...prev, { role: 'assistant', content: resp.reply }])
    },
    onError: (err: Error) => toast.error(err.message || 'LLM-запрос не удался'),
  })

  // Optimistic-push user-сообщения ДО отправки, чтобы оно появилось мгновенно.
  // Бэку шлём `history` без только что добавленного — он ждёт его в `message`.
  const send = (message: string) => {
    const snapshot = history
    setHistory((prev) => [...prev, { role: 'user', content: message }])
    mut.mutate({ message, history: snapshot })
  }

  const reset = () => {
    setHistory([])
    setLastResponse(null)
    mut.reset()
  }

  return {
    history,
    lastResponse,
    isPending: mut.isPending,
    send,
    reset,
  }
}
