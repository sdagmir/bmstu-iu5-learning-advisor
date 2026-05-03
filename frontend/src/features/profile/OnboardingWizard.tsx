import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CircleNotch } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { CareerGoalSection } from './sections/CareerGoalSection'
import { SemesterSection } from './sections/SemesterSection'
import { TechnoparkSection } from './sections/TechnoparkSection'
import { WorkloadSection } from './sections/WorkloadSection'
import { isProfileMinimallyComplete, useProfile } from './useProfile'
import { useAuthStore } from '@/stores/authStore'
import { routes } from '@/constants/routes'
import { cn } from '@/lib/utils'
import type {
  CareerGoal,
  ProfileUpdate,
  TechparkStatus,
  WorkloadPref,
} from '@/types/api'

interface Draft {
  career_goal: CareerGoal | null
  semester: number | null
  technopark_status: TechparkStatus | null
  workload_pref: WorkloadPref | null
}

const TOTAL_FIELD_STEPS = 4

/**
 * Онбординг: пять экранов — welcome + 4 поля X1–X4.
 * PATCH каждого поля сразу на «Дальше» — если пользователь закроет вкладку,
 * прогресс сохранён, при следующем заходе автоматически попадёт на нужный шаг.
 */
export function OnboardingWizard() {
  const navigate = useNavigate()
  const { patchMe } = useProfile()
  const [stepIdx, setStepIdx] = useState(0) // 0 = welcome, 1..4 = поля

  // Lazy initializer — читаем профиль один раз при mount, без подписки.
  // Дальше wizard работает с локальным draft; обновления authStore не вызывают
  // re-render всего wizard'а.
  const [draft, setDraft] = useState<Draft>(() => {
    const u = useAuthStore.getState().user
    return {
      career_goal: u?.career_goal ?? null,
      semester: u?.semester ?? null,
      technopark_status: u?.technopark_status ?? null,
      workload_pref: u?.workload_pref ?? null,
    }
  })
  const [error, setError] = useState<string | null>(null)

  // Узкая подписка только на «полнота профиля» — boolean. Меняется один раз,
  // когда профиль становится полным (после последнего шага), и тогда редиректим.
  const isComplete = useAuthStore((s) => isProfileMinimallyComplete(s.user))
  useEffect(() => {
    if (isComplete) {
      navigate(routes.home, { replace: true })
    }
  }, [isComplete, navigate])

  const advance = async (update: ProfileUpdate) => {
    setError(null)
    setDraft((d) => ({ ...d, ...update }))
    try {
      await patchMe.mutateAsync(update)
      if (stepIdx >= TOTAL_FIELD_STEPS) {
        navigate(routes.home, { replace: true })
      } else {
        setStepIdx((i) => i + 1)
      }
    } catch {
      setError('Не удалось сохранить. Проверь соединение и попробуй ещё раз.')
    }
  }

  const goBack = () => {
    setError(null)
    setStepIdx((i) => Math.max(0, i - 1))
  }

  return (
    <div className="mx-auto flex max-w-[520px] flex-col px-[var(--space-xl)] pt-[clamp(64px,15vh,160px)] pb-[var(--space-3xl)]">
      {stepIdx > 0 && (
        <div className="mb-[var(--space-2xl)]">
          <div className="mb-[var(--space-sm)] flex items-center justify-between text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            <span>
              Шаг {stepIdx} из {TOTAL_FIELD_STEPS}
            </span>
          </div>
          <div className="flex gap-[6px]" aria-hidden>
            {Array.from({ length: TOTAL_FIELD_STEPS }, (_, i) => (
              <div
                key={i}
                className={cn(
                  'h-[3px] flex-1 rounded-full transition-colors',
                  i < stepIdx
                    ? 'bg-[color:var(--color-primary)]'
                    : 'bg-[color:var(--color-border)]',
                )}
              />
            ))}
          </div>
        </div>
      )}

      {stepIdx === 0 && <WelcomeStep onStart={() => setStepIdx(1)} />}

      {stepIdx === 1 && (
        <StepLayout
          heading="Кем ты хочешь стать?"
          intro="Карьерная цель определяет всё дальше — какие курсы ЦК, какой трек Технопарка и темы курсовых система предложит."
          onBack={goBack}
          onNext={() => {
            if (draft.career_goal) advance({ career_goal: draft.career_goal })
          }}
          canAdvance={draft.career_goal !== null}
          isPending={patchMe.isPending}
          error={error}
        >
          <CareerGoalSection
            value={draft.career_goal}
            onChange={(v) => setDraft((d) => ({ ...d, career_goal: v }))}
          />
        </StepLayout>
      )}

      {stepIdx === 2 && (
        <StepLayout
          heading="На каком ты семестре?"
          intro="От семестра зависит, какие дисциплины и темы курсовых актуальны прямо сейчас."
          onBack={goBack}
          onNext={() => {
            if (draft.semester !== null) advance({ semester: draft.semester })
          }}
          canAdvance={draft.semester !== null}
          isPending={patchMe.isPending}
          error={error}
        >
          <SemesterSection
            value={draft.semester}
            onChange={(v) => setDraft((d) => ({ ...d, semester: v }))}
          />
        </StepLayout>
      )}

      {stepIdx === 3 && (
        <StepLayout
          heading="Технопарк?"
          intro="Если уже на каком-то треке — отметь. Если нет — выбери «Не участвую», система может посоветовать подходящий."
          onBack={goBack}
          onNext={() => {
            if (draft.technopark_status !== null)
              advance({ technopark_status: draft.technopark_status })
          }}
          canAdvance={draft.technopark_status !== null}
          isPending={patchMe.isPending}
          error={error}
        >
          <TechnoparkSection
            value={draft.technopark_status}
            onChange={(v) => setDraft((d) => ({ ...d, technopark_status: v }))}
          />
        </StepLayout>
      )}

      {stepIdx === 4 && (
        <StepLayout
          heading="Какая нагрузка комфортна?"
          intro="Это скажет системе, как агрессивно набирать дополнительные курсы поверх учебного плана."
          onBack={goBack}
          onNext={() => {
            if (draft.workload_pref !== null)
              advance({ workload_pref: draft.workload_pref })
          }}
          canAdvance={draft.workload_pref !== null}
          isPending={patchMe.isPending}
          error={error}
          isLast
        >
          <WorkloadSection
            value={draft.workload_pref}
            onChange={(v) => setDraft((d) => ({ ...d, workload_pref: v }))}
          />
        </StepLayout>
      )}
    </div>
  )
}

function WelcomeStep({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      <h1 className="font-serif text-[length:var(--text-3xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
        Привет
      </h1>
      <p className="text-[length:var(--text-md)] leading-relaxed text-[color:var(--color-text-muted)]">
        Чтобы подобрать рекомендации, спрошу о четырёх вещах: карьерная цель,
        семестр, Технопарк и комфортная нагрузка. Меньше минуты — и можно
        начинать.
      </p>
      <Button
        type="button"
        onClick={onStart}
        className="mt-[var(--space-base)] h-10 w-fit text-[length:var(--text-base)]"
      >
        Начнём
        <ArrowRight size={16} weight="regular" />
      </Button>
    </div>
  )
}

interface StepLayoutProps {
  heading: string
  intro: string
  children: ReactNode
  onBack: () => void
  onNext: () => void
  canAdvance: boolean
  isPending: boolean
  error: string | null
  isLast?: boolean
}

function StepLayout({
  heading,
  intro,
  children,
  onBack,
  onNext,
  canAdvance,
  isPending,
  error,
  isLast,
}: StepLayoutProps) {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      <div>
        <h1 className="mb-[var(--space-sm)] font-serif text-[length:var(--text-2xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
          {heading}
        </h1>
        <p className="text-[length:var(--text-base)] text-[color:var(--color-text-muted)]">
          {intro}
        </p>
      </div>

      {children}

      {error && (
        <p
          role="alert"
          className="text-[length:var(--text-sm)] text-[color:var(--color-danger)]"
        >
          {error}
        </p>
      )}

      <div className="mt-[var(--space-base)] flex items-center justify-between">
        <Button type="button" variant="ghost" onClick={onBack} disabled={isPending}>
          <ArrowLeft size={16} weight="regular" />
          Назад
        </Button>
        <Button
          type="button"
          onClick={onNext}
          disabled={!canAdvance || isPending}
          className="h-10 text-[length:var(--text-base)]"
        >
          {isPending ? (
            <CircleNotch size={16} weight="regular" className="animate-spin" />
          ) : null}
          {isLast ? 'Готово' : 'Дальше'}
          {!isPending && !isLast && <ArrowRight size={16} weight="regular" />}
        </Button>
      </div>
    </div>
  )
}
