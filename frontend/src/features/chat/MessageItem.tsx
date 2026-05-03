import { WarningCircle } from '@phosphor-icons/react'
import type { ChatMessage } from './useChatSession'

interface MessageItemProps {
  message: ChatMessage
}

/**
 * Одно сообщение в ленте.
 * - user: справа, до 60% ширины, тинт-фон, rounded
 * - assistant: слева full-width до 72ch, без подложки, ассистент = «продолжение текста»
 * - error: inline-маркер ошибки, danger-цвет, без bubble
 */
export function MessageItem({ message }: MessageItemProps) {
  if (message.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-[10px] bg-[color:var(--color-primary-soft)] px-[var(--space-base)] py-[var(--space-sm)] text-[length:var(--text-base)] leading-relaxed whitespace-pre-wrap text-[color:var(--color-text)] sm:max-w-[60%]">
          {message.content}
        </div>
      </div>
    )
  }
  if (message.role === 'error') {
    return (
      <div className="flex items-start gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-danger)]">
        <WarningCircle size={14} weight="bold" className="mt-[3px] shrink-0" />
        <span>{message.content}</span>
      </div>
    )
  }
  // assistant
  return (
    <div className="max-w-[72ch] text-[length:var(--text-base)] leading-relaxed whitespace-pre-wrap text-[color:var(--color-text)]">
      {message.content}
    </div>
  )
}
