import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { Target } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useAuthStore } from '@/stores/authStore'
import { useCoverage } from '@/features/coverage/useCoverage'
import { COMPETENCY_CATEGORY_LABELS } from '@/constants/enums'
import { routes } from '@/constants/routes'
import { cn } from '@/lib/utils'
import type { CompetencyCoverageItem } from '@/types/api'

/**
 * Радар компетенций. Показывает три блока:
 *  - **Пробелы** — нужно для цели, но ещё не освоено (приоритет)
 *  - **Закрыто** — нужно и освоено
 *  - **Бонус** — освоено, но в целевом профиле не значится
 *
 * «Освоено» на бэке = пройденные ЦК + дисциплины с оценкой ≥ 4.
 */
export default function CoveragePage() {
  const careerGoal = useAuthStore((s) => s.user?.career_goal ?? null)
  const { data, isLoading, isError } = useCoverage()

  const groups = useMemo(() => groupItems(data?.items ?? []), [data])

  if (!careerGoal || careerGoal === 'undecided') {
    return (
      <>
        <PageTopBar title="Покрытие" />
        <EmptyHero
          title="Сначала выбери карьерную цель"
          subtitle="Без неё нечего сравнивать. Цель задаётся в профиле."
          actionLabel="В профиль"
          actionTo={routes.profile}
        />
      </>
    )
  }

  if (isLoading) {
    return (
      <>
        <PageTopBar title="Покрытие" />
        <div className="mx-auto flex w-full max-w-[920px] flex-col gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-xl)]">
          <Skeleton className="h-12 w-1/2" />
          <Skeleton className="h-2 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      </>
    )
  }

  if (isError || !data) {
    return (
      <>
        <PageTopBar title="Покрытие" />
        <EmptyHero
          title="Не удалось загрузить покрытие"
          subtitle="Попробуй обновить страницу. Если повторится — напиши в чат."
          actionLabel="На главную"
          actionTo={routes.home}
        />
      </>
    )
  }

  const total = data.items.length
  const percent = data.coverage_percent

  return (
    <>
      <PageTopBar title="Покрытие" />
      <div className="mx-auto flex w-full max-w-[920px] flex-col gap-[var(--space-2xl)] px-[var(--space-2xl)] py-[var(--space-xl)]">
        <header className="flex flex-col gap-[var(--space-base)]">
          <div className="flex items-baseline gap-[var(--space-md)]">
            <Target
              size={28}
              weight="regular"
              className="text-[color:var(--color-primary)]"
            />
            <h1 className="font-serif text-[length:var(--text-2xl)] font-semibold text-[color:var(--color-text)]">
              <span className="tabular-nums">{percent.toFixed(1)}%</span>{' '}
              <span className="font-normal text-[color:var(--color-text-muted)]">
                целевого профиля закрыто
              </span>
            </h1>
          </div>
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            {groups.gaps.length > 0
              ? `${groups.gaps.length} компетенций для цели ещё не освоено — закрой их через ЦК или хорошие оценки в дисциплинах.`
              : 'Все целевые компетенции освоены — отличный результат.'}
          </p>
          <ProgressBar value={percent} />
        </header>

        {groups.gaps.length > 0 && (
          <Section
            title="Пробелы"
            count={groups.gaps.length}
            tone="danger"
            description="Нужно для цели — пока не освоено"
            items={groups.gaps}
          />
        )}
        {groups.covered.length > 0 && (
          <Section
            title="Закрыто"
            count={groups.covered.length}
            tone="ok"
            description="Нужно для цели — уже освоено"
            items={groups.covered}
          />
        )}
        {groups.bonus.length > 0 && (
          <Section
            title="Бонус"
            count={groups.bonus.length}
            tone="muted"
            description="Освоено, но в целевом профиле не значится"
            items={groups.bonus}
          />
        )}

        {total === 0 && (
          <p className="rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-lg)] text-center text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
            Пусто. Заполни оценки и пройденные ЦК — здесь появится разбивка.
          </p>
        )}
      </div>
    </>
  )
}

interface Groups {
  gaps: CompetencyCoverageItem[]
  covered: CompetencyCoverageItem[]
  bonus: CompetencyCoverageItem[]
}

function groupItems(items: CompetencyCoverageItem[]): Groups {
  const gaps: CompetencyCoverageItem[] = []
  const covered: CompetencyCoverageItem[] = []
  const bonus: CompetencyCoverageItem[] = []
  for (const it of items) {
    if (it.needed && !it.has) gaps.push(it)
    else if (it.needed && it.has) covered.push(it)
    else if (!it.needed && it.has) bonus.push(it)
  }
  const byName = (a: CompetencyCoverageItem, b: CompetencyCoverageItem) =>
    a.name.localeCompare(b.name, 'ru')
  return {
    gaps: gaps.sort(byName),
    covered: covered.sort(byName),
    bonus: bonus.sort(byName),
  }
}

interface SectionProps {
  title: string
  count: number
  tone: 'ok' | 'danger' | 'muted'
  description: string
  items: CompetencyCoverageItem[]
}

function Section({ title, count, tone, description, items }: SectionProps) {
  return (
    <section className="flex flex-col gap-[var(--space-md)]">
      <header className="flex items-baseline justify-between gap-[var(--space-base)]">
        <div className="flex items-baseline gap-[var(--space-sm)]">
          <h2
            className={cn(
              'font-serif text-[length:var(--text-lg)] font-semibold',
              tone === 'danger' && 'text-[color:var(--color-danger)]',
              tone === 'ok' && 'text-[color:var(--color-text)]',
              tone === 'muted' && 'text-[color:var(--color-text-muted)]',
            )}
          >
            {title}
          </h2>
          <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)] tabular-nums">
            · {count}
          </span>
        </div>
      </header>
      <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        {description}
      </p>
      <ul className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-[var(--space-sm)]">
        {items.map((it) => (
          <li
            key={it.competency_id}
            className={cn(
              'flex flex-col gap-[2px] rounded-[6px] border bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)]',
              tone === 'danger' && 'border-[color:var(--color-danger)]/30',
              tone === 'ok' && 'border-[color:var(--color-border)]',
              tone === 'muted' && 'border-[color:var(--color-border)]',
            )}
          >
            <span className="text-[length:var(--text-sm)] font-medium text-[color:var(--color-text)]">
              {it.name}
            </span>
            <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
              {COMPETENCY_CATEGORY_LABELS[it.category]}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

function ProgressBar({ value }: { value: number }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-[color:var(--color-surface-muted)]">
      <div
        className="h-full rounded-full bg-[color:var(--color-primary)] transition-[width] duration-500"
        style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
      />
    </div>
  )
}

interface EmptyHeroProps {
  title: string
  subtitle: string
  actionLabel: string
  actionTo: string
}

function EmptyHero({ title, subtitle, actionLabel, actionTo }: EmptyHeroProps) {
  return (
    <div className="mx-auto flex max-w-[600px] flex-col items-center gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-3xl)] text-center">
      <div className="flex flex-col gap-[var(--space-sm)]">
        <h1 className="font-serif text-[length:var(--text-xl)] font-semibold text-[color:var(--color-text)]">
          {title}
        </h1>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          {subtitle}
        </p>
      </div>
      <Button asChild variant="outline">
        <Link to={actionTo}>{actionLabel}</Link>
      </Button>
    </div>
  )
}
