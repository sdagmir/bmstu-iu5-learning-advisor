import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CaretDown, CaretRight } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { RecommendationCard } from '@/features/recommendation/RecommendationCard'
import { useRecommendationHistory } from '@/features/history/useHistory'
import { routes } from '@/constants/routes'
import { cn } from '@/lib/utils'
import type { RecommendationSnapshot } from '@/types/api'

/**
 * Лента снапшотов рекомендаций. Бэк фиксирует snapshot при изменении X1–X4
 * (PATCH /users/me) — список здесь сортирован от свежих к старым.
 */
export default function HistoryPage() {
  const { data, isLoading, isError } = useRecommendationHistory()
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (isLoading) {
    return (
      <>
        <PageTopBar title="История" />
        <div className="mx-auto flex w-full max-w-[760px] flex-col gap-[var(--space-base)] px-[var(--space-2xl)] py-[var(--space-xl)]">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      </>
    )
  }

  if (isError || !data) {
    return (
      <>
        <PageTopBar title="История" />
        <div className="mx-auto flex max-w-[600px] flex-col items-center gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-3xl)] text-center">
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            Не удалось загрузить историю. Попробуй обновить страницу.
          </p>
          <Button asChild variant="outline">
            <Link to={routes.home}>На главную</Link>
          </Button>
        </div>
      </>
    )
  }

  if (data.length === 0) {
    return (
      <>
        <PageTopBar title="История" />
        <div className="mx-auto flex max-w-[600px] flex-col items-center gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-3xl)] text-center">
          <div className="flex flex-col gap-[var(--space-sm)]">
            <h1 className="font-serif text-[length:var(--text-xl)] font-semibold text-[color:var(--color-text)]">
              История пока пуста
            </h1>
            <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
              Снимок рекомендаций сохраняется, когда меняешь карьерную цель,
              семестр, статус Технопарка или предпочтение нагрузки.
            </p>
            <p className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
              Текущие актуальные рекомендации — на главной.
            </p>
          </div>
          <Button asChild variant="outline">
            <Link to={routes.profile}>Открыть профиль</Link>
          </Button>
        </div>
      </>
    )
  }

  return (
    <>
      <PageTopBar title="История" />
      <div className="mx-auto flex w-full max-w-[760px] flex-col gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-xl)]">
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          <span className="tabular-nums">{data.length}</span>{' '}
          {pluralize(data.length, 'снапшот', 'снапшота', 'снапшотов')}
          {' · '}сверху — самый свежий
        </p>
        <ol className="flex flex-col">
          {data.map((snap) => (
            <SnapshotEntry
              key={snap.id}
              snapshot={snap}
              isExpanded={expandedId === snap.id}
              onToggle={() =>
                setExpandedId((prev) => (prev === snap.id ? null : snap.id))
              }
            />
          ))}
        </ol>
      </div>
    </>
  )
}

interface SnapshotEntryProps {
  snapshot: RecommendationSnapshot
  isExpanded: boolean
  onToggle: () => void
}

function SnapshotEntry({ snapshot, isExpanded, onToggle }: SnapshotEntryProps) {
  const recCount = snapshot.recommendations.length
  return (
    <li className="flex flex-col border-t border-[color:var(--color-border)] py-[var(--space-base)] first:border-t-0 first:pt-0">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isExpanded}
        className="flex w-full items-start justify-between gap-[var(--space-base)] text-left"
      >
        <div className="flex min-w-0 flex-col gap-[2px]">
          <span className="text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-subtle)]">
            {formatDate(snapshot.created_at)}
          </span>
          {snapshot.profile_change_summary ? (
            <span className="text-[length:var(--text-base)] text-[color:var(--color-text)]">
              {snapshot.profile_change_summary}
            </span>
          ) : (
            <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
              Снимок профиля
            </span>
          )}
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)] tabular-nums">
            {recCount} {pluralize(recCount, 'рекомендация', 'рекомендации', 'рекомендаций')}
          </span>
        </div>
        <span
          aria-hidden="true"
          className={cn(
            'mt-[2px] flex h-6 w-6 shrink-0 items-center justify-center text-[color:var(--color-text-subtle)]',
          )}
        >
          {isExpanded ? <CaretDown size={14} /> : <CaretRight size={14} />}
        </span>
      </button>
      {isExpanded && recCount > 0 && (
        <div className="mt-[var(--space-sm)] flex flex-col">
          {snapshot.recommendations.map((rec) => (
            <RecommendationCard key={rec.rule_id} recommendation={rec} mode="user" />
          ))}
        </div>
      )}
    </li>
  )
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function pluralize(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return one
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few
  return many
}
