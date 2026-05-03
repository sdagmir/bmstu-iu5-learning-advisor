import { memo } from 'react'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import {
  ALL_TECHPARK_STATUSES,
  TECHPARK_STATUS_DESCRIPTIONS,
  TECHPARK_STATUS_LABELS,
} from '@/constants/enums'
import type { TechparkStatus } from '@/types/api'

interface Props {
  value: TechparkStatus | null
  onChange: (value: TechparkStatus) => void
  id?: string
  disabled?: boolean
}

/**
 * X3 — статус в Технопарке. RadioGroup с описаниями для каждого варианта.
 * Описание под лейблом помогает быстро выбрать без знания терминов.
 */
function TechnoparkSectionImpl({
  value,
  onChange,
  id = 'technopark',
  disabled = false,
}: Props) {
  return (
    <div className="flex flex-col gap-[var(--space-sm)]">
      <Label id={`${id}-label`}>Технопарк</Label>
      <RadioGroup
        aria-labelledby={`${id}-label`}
        onValueChange={(v) => onChange(v as TechparkStatus)}
        disabled={disabled}
        className="gap-[var(--space-sm)]"
        {...(value !== null ? { value } : {})}
      >
        {ALL_TECHPARK_STATUSES.map((s) => {
          const itemId = `${id}-${s}`
          return (
            <label
              key={s}
              htmlFor={itemId}
              className="flex cursor-pointer items-start gap-[var(--space-md)] rounded-[6px] border border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-sm)] transition-colors hover:border-[color:var(--color-border-strong)] has-data-[state=checked]:border-[color:var(--color-primary)] has-data-[state=checked]:bg-[color:var(--color-primary-soft)]"
            >
              <RadioGroupItem id={itemId} value={s} className="mt-[6px]" />
              <span className="flex flex-col gap-[2px]">
                <span className="text-[length:var(--text-base)] font-medium text-[color:var(--color-text)]">
                  {TECHPARK_STATUS_LABELS[s]}
                </span>
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                  {TECHPARK_STATUS_DESCRIPTIONS[s]}
                </span>
              </span>
            </label>
          )
        })}
      </RadioGroup>
    </div>
  )
}

export const TechnoparkSection = memo(TechnoparkSectionImpl)
