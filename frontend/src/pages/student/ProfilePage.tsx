import { useCallback } from 'react'
import { User } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { useProfile } from '@/features/profile/useProfile'
import { useAuthStore } from '@/stores/authStore'
import { SaveStatus } from '@/features/profile/SaveStatus'
import { CareerGoalSection } from '@/features/profile/sections/CareerGoalSection'
import { SemesterSection } from '@/features/profile/sections/SemesterSection'
import { TechnoparkSection } from '@/features/profile/sections/TechnoparkSection'
import { WorkloadSection } from '@/features/profile/sections/WorkloadSection'
import { GradesSection } from '@/features/profile/sections/GradesSection'
import { CompletedCKSection } from '@/features/profile/sections/CompletedCKSection'
import type { CareerGoal, TechparkStatus, WorkloadPref } from '@/types/api'

/**
 * Редактирование профиля. Auto-save через мутации (X1–X4 + grades + CK).
 *
 * Узкие селекторы из authStore (по одному полю на секцию) + memo на секциях
 * + стабильные onChange через useCallback (deps на стабильный `mutate`) →
 * секции пере-рендерятся только когда меняется ИХ поле, без cascade-флика.
 */
export default function ProfilePage() {
  const { patchMe } = useProfile()

  const userExists = useAuthStore((s) => s.user !== null)
  const careerGoal = useAuthStore((s) => s.user?.career_goal ?? null)
  const semester = useAuthStore((s) => s.user?.semester ?? null)
  const technoparkStatus = useAuthStore((s) => s.user?.technopark_status ?? null)
  const workloadPref = useAuthStore((s) => s.user?.workload_pref ?? null)

  // Стабильные ссылки. `mutate` из TanStack Query стабилен между рендерами,
  // поэтому useCallback с ним в deps не пересоздаётся.
  const { mutate: patchMutate } = patchMe
  const onCareerChange = useCallback(
    (v: CareerGoal) => patchMutate({ career_goal: v }),
    [patchMutate],
  )
  const onSemesterChange = useCallback(
    (v: number) => patchMutate({ semester: v }),
    [patchMutate],
  )
  const onTechnoparkChange = useCallback(
    (v: TechparkStatus) => patchMutate({ technopark_status: v }),
    [patchMutate],
  )
  const onWorkloadChange = useCallback(
    (v: WorkloadPref) => patchMutate({ workload_pref: v }),
    [patchMutate],
  )

  if (!userExists) return null

  return (
    <>
      <PageTopBar
        title="Профиль"
        icon={<User size={18} weight="regular" />}
        actions={<SaveStatus />}
      />
      <div className="mx-auto max-w-[1040px] px-[var(--space-2xl)] py-[var(--space-2xl)]">
        <PageHeader
          title="Твой профиль"
          description="Изменения сохраняются автоматически. После любой правки система пересчитает рекомендации."
        />

        <div className="flex max-w-[640px] flex-col gap-[var(--space-2xl)]">
          <CareerGoalSection value={careerGoal} onChange={onCareerChange} />
          <SemesterSection value={semester} onChange={onSemesterChange} />
          <TechnoparkSection value={technoparkStatus} onChange={onTechnoparkChange} />
          <WorkloadSection value={workloadPref} onChange={onWorkloadChange} />
          <GradesSection />
          <CompletedCKSection />
        </div>
      </div>
    </>
  )
}
