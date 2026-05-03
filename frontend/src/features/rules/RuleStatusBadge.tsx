import { cn } from '@/lib/utils'

interface RuleStatusBadgeProps {
  isPublished: boolean
  isActive: boolean
  className?: string
}

/**
 * Бейдж статуса правила. Три варианта:
 *  - draft (черновик): muted-окантовка, серый текст
 *  - published & active: зелёный (success-soft)
 *  - published & inactive: жёлтый (warning-soft) — kill-switch выключил движок
 *
 * Никаких side-stripe: только заливка + тонкий бордер. Без uppercase
 * на основном тексте — uppercase tracking-wider читается агрессивно
 * рядом с моноспейсом R-номера. Используем регулярный case + tabular weight.
 */
export function RuleStatusBadge({ isPublished, isActive, className }: RuleStatusBadgeProps) {
  if (!isPublished) {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-[4px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[2px] text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]',
          className,
        )}
      >
        Черновик
      </span>
    )
  }
  if (isActive) {
    return (
      <span
        className={cn(
          'inline-flex items-center rounded-[4px] bg-[color:var(--color-success-soft)] px-[var(--space-sm)] py-[2px] text-[length:var(--text-xs)] font-medium text-[color:var(--color-success)]',
          className,
        )}
      >
        Опубликовано
      </span>
    )
  }
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-[4px] bg-[color:var(--color-warning-soft)] px-[var(--space-sm)] py-[2px] text-[length:var(--text-xs)] font-medium text-[color:var(--color-warning)]',
        className,
      )}
    >
      Опубликовано · выключено
    </span>
  )
}
