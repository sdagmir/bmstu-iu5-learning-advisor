import { useState, type ReactNode } from 'react'
import { CaretRight } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'

interface CollapsibleGroupProps {
  /** Заголовок группы — uppercase tracking, как у наших секционных меток. */
  title: ReactNode
  /** Опциональный правый край: прогресс-счётчик `2/6`, статус и т.п. */
  meta?: ReactNode
  defaultOpen?: boolean
  children: ReactNode
}

/**
 * Раскрывающаяся группа. Кликабельный header с caret-индикатором, контент
 * показывается при `open=true`. Используется в GradesSection (по семестрам)
 * и CompletedCKSection (по категориям ЦК).
 */
export function CollapsibleGroup({
  title,
  meta,
  defaultOpen = true,
  children,
}: CollapsibleGroupProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className="flex flex-col">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="group flex w-full cursor-pointer items-center gap-[var(--space-sm)] rounded-[6px] px-[var(--space-xs)] py-[var(--space-xs)] text-left transition-colors hover:bg-[color:var(--color-surface-muted)]"
      >
        <CaretRight
          size={12}
          weight="bold"
          className={cn(
            'shrink-0 text-[color:var(--color-text-subtle)] transition-transform duration-150',
            open && 'rotate-90',
          )}
        />
        <span className="flex-1 text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          {title}
        </span>
        {meta != null && (
          <span className="shrink-0 text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-subtle)]">
            {meta}
          </span>
        )}
      </button>
      {open && <div className="pt-[var(--space-xs)]">{children}</div>}
    </div>
  )
}
