import { useEffect, useRef } from 'react'
import { MessageItem } from './MessageItem'
import type { ChatMessage } from './useChatSession'

interface ChatLentProps {
  messages: ChatMessage[]
  isPending: boolean
}

/**
 * Скроллируемая лента сообщений. Auto-scroll к низу при появлении новых
 * сообщений или начале «думания». Свой overflow-y-auto, чтобы лента
 * скроллилась независимо от input-bar и topbar.
 */
export function ChatLent({ messages, isPending }: ChatLentProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = scrollRef.current
    if (!el) return
    el.scrollTop = el.scrollHeight
  }, [messages.length, isPending])

  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto">
      <div className="mx-auto flex max-w-[720px] flex-col gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-xl)]">
        {messages.map((m) => (
          <MessageItem key={m.id} message={m} />
        ))}
        {isPending && <ThinkingIndicator />}
      </div>
    </div>
  )
}

/** «Думаю...» — три точки, пульсация. Появляется под последней user-репликой. */
function ThinkingIndicator() {
  return (
    <div
      className="flex items-center gap-[var(--space-xs)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]"
      role="status"
      aria-live="polite"
    >
      <span className="sr-only">Ассистент печатает</span>
      <span className="flex gap-[3px]" aria-hidden>
        <Dot delay="0ms" />
        <Dot delay="150ms" />
        <Dot delay="300ms" />
      </span>
    </div>
  )
}

function Dot({ delay }: { delay: string }) {
  return (
    <span
      className="block h-[6px] w-[6px] rounded-full bg-[color:var(--color-text-muted)] [animation-delay:var(--delay)] [animation-duration:1.2s] [animation-iteration-count:infinite] [animation-name:pulse]"
      style={{ ['--delay' as string]: delay }}
    />
  )
}
