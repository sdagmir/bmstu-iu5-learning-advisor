import { memo } from 'react'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Label } from '@/components/ui/label'
import {
  ALL_WORKLOAD_PREFS,
  WORKLOAD_PREF_DESCRIPTIONS,
  WORKLOAD_PREF_LABELS,
} from '@/constants/enums'
import type { WorkloadPref } from '@/types/api'

interface Props {
  value: WorkloadPref | null
  onChange: (value: WorkloadPref) => void
  id?: string
  disabled?: boolean
}

/**
 * X4 — предпочтение нагрузки.
 */
function WorkloadSectionImpl({
  value,
  onChange,
  id = 'workload',
  disabled = false,
}: Props) {
  return (
    <div className="flex flex-col gap-[var(--space-sm)]">
      <Label id={`${id}-label`}>Нагрузка</Label>
      <RadioGroup
        aria-labelledby={`${id}-label`}
        onValueChange={(v) => onChange(v as WorkloadPref)}
        disabled={disabled}
        className="gap-[var(--space-sm)]"
        {...(value !== null ? { value } : {})}
      >
        {ALL_WORKLOAD_PREFS.map((s) => {
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
                  {WORKLOAD_PREF_LABELS[s]}
                </span>
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                  {WORKLOAD_PREF_DESCRIPTIONS[s]}
                </span>
              </span>
            </label>
          )
        })}
      </RadioGroup>
    </div>
  )
}

export const WorkloadSection = memo(WorkloadSectionImpl)
