import { memo } from 'react'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface Props {
  value: number | null
  onChange: (value: number) => void
  id?: string
  disabled?: boolean
}

const SEMESTERS = [1, 2, 3, 4, 5, 6, 7, 8] as const

/**
 * X2 — семестр. Сегментированный контрол размером по контенту,
 * не тянется на всю ширину формы (size = importance).
 */
function SemesterSectionImpl({
  value,
  onChange,
  id = 'semester',
  disabled = false,
}: Props) {
  return (
    <div className="flex flex-col gap-[var(--space-sm)]">
      <Label id={`${id}-label`}>Семестр</Label>
      <div
        role="radiogroup"
        aria-labelledby={`${id}-label`}
        className="flex flex-wrap gap-[var(--space-xs)]"
      >
        {SEMESTERS.map((s) => {
          const selected = s === value
          return (
            <button
              key={s}
              type="button"
              role="radio"
              aria-checked={selected}
              disabled={disabled}
              onClick={() => onChange(s)}
              className={cn(
                'flex h-10 w-10 items-center justify-center rounded-[6px] border text-[length:var(--text-base)] tabular-nums transition-colors',
                selected
                  ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary-soft)] font-semibold text-[color:var(--color-primary)]'
                  : 'border-[color:var(--color-border)] text-[color:var(--color-text-muted)] hover:border-[color:var(--color-border-strong)] hover:text-[color:var(--color-text)]',
                disabled && 'cursor-not-allowed opacity-50',
              )}
            >
              {s}
            </button>
          )
        })}
      </div>
    </div>
  )
}

export const SemesterSection = memo(SemesterSectionImpl)
