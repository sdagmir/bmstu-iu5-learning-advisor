import { useEffect, useRef, useState } from 'react'
import { PaperPlaneTilt, CircleNotch } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface InputBarProps {
  onSend: (text: string) => void
  isPending: boolean
}

const MAX_HEIGHT = 240

/**
 * Поле ввода чата. Кнопка отправки ВНУТРИ rounded-контейнера (не отделена сбоку).
 * Высота подстраивается под содержимое: одна строка = ~52px, растёт до 240px и
 * дальше скроллится без видимого скроллбара. Полотно единое — без border-t
 * сверху, никаких визуальных швов.
 *
 * Hotkey ⌘/Ctrl+Enter — отправка. Plain Enter — перенос строки.
 */
export function InputBar({ onSend, isPending }: InputBarProps) {
  const [text, setText] = useState('')
  const taRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const ta = taRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, MAX_HEIGHT)}px`
  }, [text])

  const submit = () => {
    const trimmed = text.trim()
    if (!trimmed || isPending) return
    onSend(trimmed)
    setText('')
  }

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      submit()
    }
  }

  const canSend = text.trim().length > 0 && !isPending

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
      className="w-full"
    >
      <div className="flex items-end gap-[var(--space-sm)] rounded-[14px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-sm)] transition-colors focus-within:border-[color:var(--color-primary)] focus-within:ring-2 focus-within:ring-[color:var(--color-primary-soft)]">
        <textarea
          ref={taRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={isPending}
          placeholder="Спроси меня о траектории…"
          rows={1}
          className={cn(
            'flex-1 resize-none border-0 bg-transparent px-[var(--space-sm)] py-[var(--space-sm)]',
            'text-[length:var(--text-base)] leading-relaxed text-[color:var(--color-text)]',
            'outline-none placeholder:text-[color:var(--color-text-subtle)]',
            'disabled:cursor-not-allowed disabled:opacity-60',
            // скрываем скроллбар (Firefox / WebKit)
            '[scrollbar-width:none] [&::-webkit-scrollbar]:hidden',
          )}
        />
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              type="submit"
              size="icon-sm"
              disabled={!canSend}
              aria-label="Отправить сообщение"
              className="h-9 w-9 shrink-0"
            >
              {isPending ? (
                <CircleNotch size={14} weight="regular" className="animate-spin" />
              ) : (
                <PaperPlaneTilt size={14} weight="regular" />
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="top">Отправить · ⌘ Enter</TooltipContent>
        </Tooltip>
      </div>
    </form>
  )
}
