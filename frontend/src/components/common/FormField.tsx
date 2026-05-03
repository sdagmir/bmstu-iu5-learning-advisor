import type { ReactNode } from 'react'
import { Label } from '@/components/ui/label'

interface FormFieldProps {
  /** id связан с input'ом; ошибка получает id `${id}-error` для aria-describedby. */
  id: string
  label: string
  error?: string | undefined
  /** Подсказка под полем. Скрывается, когда есть ошибка. */
  hint?: string
  children: ReactNode
}

/**
 * Универсальная обёртка для поля формы: Label сверху, контрол посередине,
 * inline-сообщение об ошибке (или подсказка) снизу. Соответствует принципу
 * impeccable interaction-design: «Errors below fields, aria-describedby».
 *
 * Сам Input/Select подключает `id={id}` и `aria-describedby={`${id}-error`}`
 * при наличии ошибки — это явное соединение, а не магия через cloneElement.
 */
export function FormField({ id, label, error, hint, children }: FormFieldProps) {
  return (
    <div className="flex flex-col gap-[var(--space-xs)]">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? (
        <p
          id={`${id}-error`}
          role="alert"
          className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]"
        >
          {error}
        </p>
      ) : hint ? (
        <p
          id={`${id}-hint`}
          className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]"
        >
          {hint}
        </p>
      ) : null}
    </div>
  )
}
