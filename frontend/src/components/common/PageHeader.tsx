import type { ReactNode } from 'react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: ReactNode
}

/** Единый заголовок страницы. Используется на всех основных экранах. */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <header className="mb-[var(--space-2xl)] flex items-start justify-between gap-[var(--space-lg)]">
      <div className="max-w-[68ch]">
        <h1 className="font-serif text-[length:var(--text-2xl)] font-semibold text-[color:var(--color-text)]">
          {title}
        </h1>
        {description && (
          <p className="mt-[var(--space-sm)] text-[length:var(--text-base)] text-[color:var(--color-text-muted)]">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="shrink-0">{actions}</div>}
    </header>
  )
}
