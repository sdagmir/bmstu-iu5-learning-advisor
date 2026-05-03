import { memo } from 'react'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import type { CareerGoal } from '@/types/api'
import { ALL_CAREER_GOALS, CAREER_GOAL_LABELS } from '@/constants/enums'

interface Props {
  value: CareerGoal | null
  onChange: (value: CareerGoal) => void
  id?: string
  disabled?: boolean
}

/**
 * X1 — карьерная цель. Контролируемый компонент: value/onChange приходят
 * сверху, секция не лезет в API сама. memo чтобы не пере-рендериться при
 * изменении соседних полей профиля.
 */
function CareerGoalSectionImpl({
  value,
  onChange,
  id = 'career-goal',
  disabled = false,
}: Props) {
  return (
    <div className="flex flex-col gap-[var(--space-sm)]">
      <Label htmlFor={id}>Карьерная цель</Label>
      <Select
        onValueChange={(v) => onChange(v as CareerGoal)}
        disabled={disabled}
        {...(value !== null ? { value } : {})}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder="Выбери направление" />
        </SelectTrigger>
        <SelectContent>
          {ALL_CAREER_GOALS.map((goal) => (
            <SelectItem key={goal} value={goal}>
              {CAREER_GOAL_LABELS[goal]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

export const CareerGoalSection = memo(CareerGoalSectionImpl)
