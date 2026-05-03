import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  description?: string
  action?: ReactNode
}

/** Пустое состояние. Вместо «ничего нет» — учим интерфейсу. */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex min-h-[320px] flex-col items-start justify-center gap-[var(--space-base)] py-[var(--space-3xl)]">
      <h2 className="font-serif text-[length:var(--text-lg)] font-semibold text-[color:var(--color-text)]">
        {title}
      </h2>
      {description && (
        <p className="max-w-[60ch] text-[length:var(--text-base)] text-[color:var(--color-text-muted)]">
          {description}
        </p>
      )}
      {action && <div className="mt-[var(--space-sm)]">{action}</div>}
    </div>
  )
}
