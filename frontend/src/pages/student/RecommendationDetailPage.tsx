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

            {/* Meta-строка курса — повторяет карточку с главной, но полнее.
                Показываем только когда linked_course пришёл (только category=ck_course
                с совпавшим title). */}
            {rec.linked_course && (
              <p className="text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
                {rec.linked_course.credits} ЕЗ · программа ЦК
              </p>
            )}

            {/* Обоснование — почему именно эта рекомендация студенту */}
            <section className="flex flex-col gap-[var(--space-xs)]">
              <h2 className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                Почему рекомендуем
              </h2>
              <p className="text-[length:var(--text-md)] leading-relaxed text-[color:var(--color-text)]">
                {rec.reasoning}
              </p>
            </section>

            {/* О программе — описание курса из БД. Только для category=ck_course
                с непустым description. Здесь, в отличие от карточки, разворачиваем
                сразу — деталка для того и нужна. */}
            {rec.linked_course?.description && (
              <section className="flex flex-col gap-[var(--space-xs)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
                <h2 className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                  О программе
                </h2>
                <p className="text-[length:var(--text-md)] leading-relaxed text-[color:var(--color-text)]">
                  {rec.linked_course.description}
                </p>
              </section>
            )}

            {/* Подсказка про карьерный gap — кликабельная, ведёт на /coverage,
                чтобы студент увидел свой прогресс по компетенциям. UID не показываем —
                это не для глаз пользователя. */}
            {rec.competency_gap && (
              <section className="flex flex-col gap-[var(--space-xs)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
                <h2 className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                  Закрывает пробел
                </h2>
                <p className="text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text-muted)]">
                  Эта рекомендация закрывает компетенцию из твоего целевого
                  профиля. Полный список покрытия —{' '}
                  <Link
                    to={routes.coverage}
                    className="text-[color:var(--color-primary)] underline-offset-4 hover:underline focus-visible:underline"
                  >
                    в радаре компетенций
                  </Link>
                  .
                </p>
              </section>
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
