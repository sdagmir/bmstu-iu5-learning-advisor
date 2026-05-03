import { useState } from 'react'
import { Check, X, CaretDown } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import type { TraceEntry } from '@/types/api'

interface RulesTracePanelProps {
  entries: TraceEntry[] | null
  totalChecked: number
  totalFired: number
}

/**
 * Список всех 52 правил с результатом прогона: сработавшие сверху (полужирные),
 * остальные — приглушённо ниже. Клик по строке раскрывает skip-reason.
 *
 * Defense-визуальная цель: показать комиссии что система детерминированная —
 * каждое правило либо fired либо есть конкретная причина почему нет.
 */
export function RulesTracePanel({
  entries,
  totalChecked,
  totalFired,
}: RulesTracePanelProps) {
  if (entries === null) {
    return (
      <div className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
        Заполни профиль слева — справа появится trace.
      </div>
    )
  }

  // Сначала fired (отсортированные по rule_id), потом skipped
  const fired = entries.filter((e) => e.fired).sort((a, b) => a.rule.localeCompare(b.rule))
  const skipped = entries.filter((e) => !e.fired).sort((a, b) => a.rule.localeCompare(b.rule))

  return (
    <div className="flex flex-col gap-[var(--space-base)]">
      <div className="flex items-baseline gap-[var(--space-sm)] border-b border-[color:var(--color-border)] pb-[var(--space-sm)]">
        <span className="font-serif text-[length:var(--text-md)] font-semibold text-[color:var(--color-text)] tabular-nums">
          {totalFired}
        </span>
        <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          из {totalChecked} правил сработало
        </span>
      </div>

      {fired.length > 0 && (
        <div className="flex flex-col gap-[var(--space-xs)]">
          <div className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
            Сработавшие
          </div>
          <ul className="flex flex-col">
            {fired.map((e) => (
              <RuleEntryRow key={e.rule} entry={e} />
            ))}
          </ul>
        </div>
      )}

      {skipped.length > 0 && (
        <div className="flex flex-col gap-[var(--space-xs)]">
          <div className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
            Не сработали
          </div>
          <ul className="flex flex-col">
            {skipped.map((e) => (
              <RuleEntryRow key={e.rule} entry={e} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function RuleEntryRow({ entry }: { entry: TraceEntry }) {
  const [expanded, setExpanded] = useState(false)
  const canExpand = !entry.fired && entry.skipped_reason

  return (
    <li className="border-b border-[color:var(--color-border)] last:border-b-0">
      <button
        type="button"
        onClick={() => canExpand && setExpanded((e) => !e)}
        className={cn(
          'flex w-full items-center gap-[var(--space-sm)] py-[var(--space-xs)] pr-[var(--space-xs)] text-left transition-colors',
          canExpand && 'cursor-pointer hover:bg-[color:var(--color-surface-muted)]',
          !canExpand && 'cursor-default',
        )}
      >
        {entry.fired ? (
          <Check
            size={12}
            weight="bold"
            className="shrink-0 text-[color:var(--color-success)]"
          />
        ) : (
          <X
            size={12}
            weight="regular"
            className="shrink-0 text-[color:var(--color-text-subtle)]"
          />
        )}
        <span
          className={cn(
            'shrink-0 font-mono text-[length:var(--text-xs)] tabular-nums',
            entry.fired
              ? 'text-[color:var(--color-text)]'
              : 'text-[color:var(--color-text-subtle)]',
          )}
        >
          {entry.rule}
        </span>
        <span
          className={cn(
            'flex-1 truncate text-[length:var(--text-sm)]',
            entry.fired
              ? 'font-medium text-[color:var(--color-text)]'
              : 'text-[color:var(--color-text-muted)]',
          )}
        >
          {entry.name}
        </span>
        {canExpand && (
          <CaretDown
            size={10}
            weight="bold"
            className={cn(
              'shrink-0 text-[color:var(--color-text-subtle)] transition-transform',
              expanded && 'rotate-180',
            )}
          />
        )}
      </button>
      {expanded && entry.skipped_reason && (
        <div className="pb-[var(--space-sm)] pl-[calc(var(--space-sm)+12px+var(--space-sm)+40px)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
          {entry.skipped_reason}
        </div>
      )}
    </li>
  )
}
