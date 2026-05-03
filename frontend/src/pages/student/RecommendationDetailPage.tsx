import { Link, useParams } from 'react-router-dom'
import { ArrowLeft } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { useRecommendations } from '@/features/recommendation/useRecommendations'
import {
  RECOMMENDATION_CATEGORY_LABELS,
  RECOMMENDATION_PRIORITY_LABELS,
} from '@/constants/enums'
import { routes } from '@/constants/routes'

/**
 * Детальная страница рекомендации. Single-column max-w-[68ch], reading-формат.
 * Данные берутся из того же кеша, что HomePage (`['expert','my-recommendations']`),
 * без отдельного эндпоинта — рекомендация ищется по rule_id.
 */
export default function RecommendationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { data, isLoading, isError } = useRecommendations()

  const rec = data?.find((r) => r.rule_id === id)

  return (
    <>
      <PageTopBar title="Рекомендация" />
      <div className="mx-auto max-w-[68ch] px-[var(--space-2xl)] py-[var(--space-2xl)]">
        <Link
          to={routes.home}
          className="mb-[var(--space-xl)] inline-flex items-center gap-[var(--space-xs)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)] transition-colors hover:text-[color:var(--color-primary)]"
        >
          <ArrowLeft size={14} weight="regular" />
          На главную
        </Link>

        {isLoading ? (
          <DetailSkeleton />
        ) : isError ? (
          <EmptyState
            title="Не удалось загрузить рекомендацию"
            description="Попробуй обновить страницу через минуту."
            action={
              <Button asChild variant="outline">
                <Link to={routes.home}>Вернуться на главную</Link>
              </Button>
            }
          />
        ) : !rec ? (
          <EmptyState
            title="Рекомендация не найдена"
            description="Возможно, она устарела после обновления профиля. Свежий список — на главной."
            action={
              <Button asChild variant="outline">
                <Link to={routes.home}>Вернуться на главную</Link>
              </Button>
            }
          />
        ) : (
          <article className="flex flex-col gap-[var(--space-lg)]">
            <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
              {RECOMMENDATION_CATEGORY_LABELS[rec.category]} ·{' '}
              {RECOMMENDATION_PRIORITY_LABELS[rec.priority]}
            </span>

            <h1 className="font-serif text-[length:var(--text-2xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
              {rec.title}
            </h1>

            <p className="text-[length:var(--text-md)] leading-relaxed text-[color:var(--color-text)]">
              {rec.reasoning}
            </p>

            {rec.competency_gap && (
              <div className="flex flex-col gap-[var(--space-xs)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
                <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                  Закрывает компетенцию
                </span>
                <span className="font-mono text-[length:var(--text-base)] text-[color:var(--color-text)]">
                  {rec.competency_gap}
                </span>
              </div>
            )}
          </article>
        )}
      </div>
    </>
  )
}

function DetailSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      <Skeleton className="h-3 w-40" />
      <Skeleton className="h-9 w-3/4" />
      <div className="flex flex-col gap-[var(--space-sm)] pt-[var(--space-sm)]">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-2/3" />
      </div>
    </div>
  )
}
