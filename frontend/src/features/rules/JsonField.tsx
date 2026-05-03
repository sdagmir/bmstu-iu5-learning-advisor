import { forwardRef, type TextareaHTMLAttributes } from 'react'
import { Warning } from '@phosphor-icons/react'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface JsonFieldProps extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, 'className'> {
  label: string
  hint?: string
  error?: string
  rows?: number
  disabled?: boolean
}

/**
 * Моноспейс-textarea для редактирования JSON. Лёгкий валидатор-под-полем
 * получает текстовую ошибку из формы (zod superRefine на conditionJson и
 * recommendationJson). Не подсвечиваем цветами синтаксис — для диплома
 * избыточно; зато читается чисто и уважительно к глазу.
 */
export const JsonField = forwardRef<HTMLTextAreaElement, JsonFieldProps>(
  function JsonField({ label, hint, error, rows = 12, disabled, ...props }, ref) {
    return (
      <div className="flex flex-col gap-[var(--space-xs)]">
        <div className="flex items-baseline justify-between gap-[var(--space-base)]">
          <Label className="text-[length:var(--text-sm)]">{label}</Label>
          {hint && (
            <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
              {hint}
            </span>
          )}
        </div>
        <textarea
          ref={ref}
          rows={rows}
          spellCheck={false}
          disabled={disabled}
          className={cn(
            'w-full resize-y rounded-[6px] border bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] font-mono text-[length:var(--text-sm)] leading-[1.55] text-[color:var(--color-text)] outline-none transition-colors',
            'focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)]',
            'disabled:cursor-not-allowed disabled:opacity-60',
            error
              ? 'border-[color:var(--color-danger)]'
              : 'border-[color:var(--color-border)]',
          )}
          {...props}
        />
        {error && (
          <span className="flex items-start gap-[var(--space-xs)] text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
            <Warning size={12} weight="regular" className="mt-[2px] shrink-0" />
            {error}
          </span>
        )}
      </div>
    )
  },
)
