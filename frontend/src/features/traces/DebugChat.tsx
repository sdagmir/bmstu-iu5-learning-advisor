import { useEffect, useRef, useState } from 'react'
import { CircleNotch, PaperPlaneTilt, ArrowCounterClockwise } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { MarkdownContent } from '@/components/common/MarkdownContent'
import type { ChatHistoryItem } from '@/types/api'

interface DebugChatProps {
  history: ChatHistoryItem[]
  isPending: boolean
  onSend: (message: string) => void
  onReset: () => void
}

/**
 * Контролируемый чат-компонент trace-инспектора. State приходит сверху,
 * чтобы DebugPanel рядом мог читать `lastResponse` от того же useDebugChat.
 */
export function DebugChat({ history, isPending, onSend, onReset }: DebugChatProps) {
  const [draft, setDraft] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  // Автоскролл при появлении новых сообщений
  useEffect(() => {
    const el = scrollRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [history.length])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!draft.trim() || isPending) return
    onSend(draft.trim())
    setDraft('')
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (draft.trim() && !isPending) {
        onSend(draft.trim())
        setDraft('')
      }
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex items-center justify-between gap-[var(--space-base)] border-b border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-sm)]">
        <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          Запрос
        </span>
        {history.length > 0 && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={isPending}
          >
            <ArrowCounterClockwise size={12} />
            Очистить
          </Button>
        )}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-[var(--space-base)] py-[var(--space-base)]"
      >
        {history.length === 0 ? (
          <div className="flex h-full items-center justify-center px-[var(--space-base)]">
            <p className="max-w-[40ch] text-center text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
              Напиши сообщение от лица студента — справа увидишь, какие правила
              и фрагменты RAG задействовала LLM.
            </p>
          </div>
        ) : (
          <ul className="flex flex-col gap-[var(--space-base)]">
            {history.map((m, i) => (
              <li
                key={i}
                className={
                  m.role === 'user'
                    ? 'flex flex-col items-end gap-[var(--space-xs)]'
                    : 'flex flex-col items-start gap-[var(--space-xs)]'
                }
              >
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                  {m.role === 'user' ? 'Студент' : 'Ассистент'}
                </span>
                {m.role === 'user' ? (
                  <div className="max-w-[85%] rounded-[8px] bg-[color:var(--color-primary-soft)] px-[var(--space-base)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed whitespace-pre-wrap text-[color:var(--color-text)]">
                    {m.content}
                  </div>
                ) : (
                  <div className="max-w-[85%] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-base)] py-[var(--space-sm)]">
                    <MarkdownContent
                      content={m.content}
                      className="text-[length:var(--text-sm)]"
                    />
                  </div>
                )}
              </li>
            ))}
            {isPending && (
              <li className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
                <CircleNotch size={14} className="animate-spin" />
                Ассистент думает…
              </li>
            )}
          </ul>
        )}
      </div>

      <form
        onSubmit={submit}
        className="border-t border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-sm)]"
      >
        <div className="flex items-end gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] focus-within:border-[color:var(--color-primary)] focus-within:ring-[3px] focus-within:ring-[color:var(--color-primary-soft)]">
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            rows={2}
            disabled={isPending}
            placeholder="Какой ЦК выбрать?"
            className="flex-1 resize-none bg-transparent text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none placeholder:text-[color:var(--color-text-subtle)] disabled:opacity-60 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
          />
          <Button
            type="submit"
            size="icon"
            disabled={isPending || !draft.trim()}
            aria-label="Отправить"
          >
            {isPending ? (
              <CircleNotch size={14} className="animate-spin" />
            ) : (
              <PaperPlaneTilt size={14} weight="fill" />
            )}
          </Button>
        </div>
        <p className="mt-[var(--space-xs)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
          ⌘↵ — отправить · Запрос идёт от твоего admin-профиля; X1–X12 берутся из БД
        </p>
      </form>
    </div>
  )
}
