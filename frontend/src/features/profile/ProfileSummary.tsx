import { useAuthStore } from '@/stores/authStore'
import {
  CAREER_GOAL_LABELS,
  TECHPARK_STATUS_LABELS,
  WORKLOAD_PREF_LABELS,
} from '@/constants/enums'

/**
 * Мета-строка ключевых полей профиля. Тонкая, в одну линию: «Цель: ML · Семестр: 5 · ...».
 * Self-subscribing: подписывается на 4 поля по отдельности (примитивы) — не
 * ре-рендерится при правке других частей профиля или email.
 */
export function ProfileSummary() {
  const careerGoal = useAuthStore((s) => s.user?.career_goal ?? null)
  const semester = useAuthStore((s) => s.user?.semester ?? null)
  const technoparkStatus = useAuthStore((s) => s.user?.technopark_status ?? null)
  const workloadPref = useAuthStore((s) => s.user?.workload_pref ?? null)

  const items: Array<{ label: string; value: string }> = []
  if (careerGoal) items.push({ label: 'Цель', value: CAREER_GOAL_LABELS[careerGoal] })
  if (semester !== null) items.push({ label: 'Семестр', value: String(semester) })
  if (technoparkStatus) {
    items.push({ label: 'Технопарк', value: TECHPARK_STATUS_LABELS[technoparkStatus] })
  }
  if (workloadPref) {
    items.push({ label: 'Нагрузка', value: WORKLOAD_PREF_LABELS[workloadPref] })
  }

  if (items.length === 0) return null

  return (
    <div className="flex flex-wrap items-center gap-x-[var(--space-base)] gap-y-[var(--space-xs)] text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
      {items.map((item, i) => (
        <span key={item.label} className="flex items-center gap-[var(--space-xs)]">
          {i > 0 && (
            <span aria-hidden className="text-[color:var(--color-text-subtle)]">
              ·
            </span>
          )}
          <span>
            {item.label}:{' '}
            <span className="font-medium text-[color:var(--color-text)]">{item.value}</span>
          </span>
        </span>
      ))}
    </div>
  )
}
