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
import { cn } from '@/lib/utils'

/**
 * Reading-параграфы для тел рекомендации (reasoning / description курса).
 * Сплитим по `\n+` — бэкенд хранит описания курсов с двойными переносами,
 * без сплита всё превращается в монолитную «кашу».
 *
 * Два режима:
 * - `lead` — вводный абзац (под title-блоком). Без indent, без justify:
 *   на коротких текстах justify рисует «реки пробелов», а красная строка
 *   после meta выглядит инородно.
 * - `body` — длинный текст в секции (после h2). Justify + hyphens-auto
 *   (браузер сам переносит русские слова при `<html lang="ru">`) + красная
 *   строка `indent-8` (2rem) у каждого абзаца, включая первый.
 */
function ProseBlock({
  text,
  className,
  variant = 'body',
}: {
  text: string
  className?: string
  variant?: 'lead' | 'body'
}) {
  const paragraphs = text
    .split(/\n+/)
    .map((p) => p.trim())
    .filter(Boolean)

  if (paragraphs.length === 0) return null

  return (
    <div className={cn('flex flex-col gap-[var(--space-base)]', className)}>
      {paragraphs.map((p, i) => (
        <p
          key={i}
          className={cn(
            'text-[length:var(--text-md)] leading-relaxed text-[color:var(--color-text)]',
            variant === 'body' && 'indent-8 hyphens-auto text-justify',
          )}
        >
          {p}
        </p>
      ))}
    </div>
  )
}

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
          /* Reading-формат: kicker → title → meta → lead-абзац (reasoning) →
             h2-секции с большим воздухом сверху → info-callout снизу.
             Никаких ALL CAPS eyebrow — иерархия только через типографику и
             пробелы, как в журнальной статье. */
          <article className="flex flex-col">
            {/* Kicker — категория · приоритет, тонкая мета над title */}
            <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
              {RECOMMENDATION_CATEGORY_LABELS[rec.category]} ·{' '}
              {RECOMMENDATION_PRIORITY_LABELS[rec.priority]}
            </span>

            <h1 className="mt-[var(--space-sm)] font-serif text-[length:var(--text-2xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
              {rec.title}
            </h1>

            {rec.linked_course && (
              <p className="mt-[var(--space-sm)] text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
                {rec.linked_course.credits} ЕЗ · курс ЦК
              </p>
            )}

            {/* Lead — reasoning сразу под title-блоком, без eyebrow. На главной
               этот же текст идёт под caption карточки — там тоже без подписи,
               сохраняем согласованность. */}
            <ProseBlock
              text={rec.reasoning}
              variant="lead"
              className="mt-[var(--space-xl)]"
            />

            {/* О программе — нормальный h2 в serif, не uppercase. Воздух сверху
               разделяет секции лучше, чем border-t. mt-2xl (не 3xl) — чтобы
               на коротком reasoning не было визуальной дыры. */}
            {rec.linked_course?.description && (
              <section className="mt-[var(--space-2xl)]">
                <h2 className="font-serif text-[length:var(--text-lg)] font-semibold tracking-tight text-[color:var(--color-text)]">
                  О курсе
                </h2>
                <ProseBlock
                  text={rec.linked_course.description}
                  className="mt-[var(--space-base)]"
                />
              </section>
            )}

            {/* Callout — связь с целевым профилем. Не секция, а info-блок:
               та же визуальная база, что у карточек на главной (bg-surface-muted
               + border + radius), маленький приглушённый текст со ссылкой. */}
            {rec.competency_gap && (
              <aside className="mt-[var(--space-2xl)] rounded-[10px] border border-[color:var(--color-border)] bg-[color:var(--color-surface-muted)] px-[var(--space-base)] py-[var(--space-base)]">
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
              </aside>
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
