import { Link } from 'react-router-dom'
import { ChatCircle, ArrowRight } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { useAuthStore } from '@/stores/authStore'
import { useRecommendations } from '@/features/recommendation/useRecommendations'
import { ProfileSummary } from '@/features/profile/ProfileSummary'
import { RecommendationCard } from '@/features/recommendation/RecommendationCard'
import { routes } from '@/constants/routes'
import type { RecommendationPriority } from '@/types/api'

/**
 * CTA-карточка «спросить в чате» в самом низу списка рекомендаций.
 *
 * Визуально — равноправный участник потока (та же hover-механика, что у
 * RecommendationCard), но с другим контентом и иконкой-маркером. Цель —
 * предложить выход для случая «среди списка нет того, что нужно», не вынося
 * это в отдельную плавающую кнопку или sticky-pill.
 */
function ChatCTACard() {
  return (
    <Link
      to={routes.chat}
      className="group flex items-center gap-[var(--space-base)] rounded-[10px] border border-transparent bg-[color:var(--color-surface-muted)] px-[var(--space-base)] py-[var(--space-base)] transition-colors hover:border-[color:var(--color-border)]"
    >
      <ChatCircle
        size={20}
        weight="regular"
        className="shrink-0 text-[color:var(--color-text-muted)] transition-colors group-hover:text-[color:var(--color-primary)]"
      />
      <div className="flex min-w-0 flex-1 flex-col gap-[2px]">
        <span className="font-serif text-[length:var(--text-base)] font-semibold tracking-tight text-[color:var(--color-text)]">
          Спросить в чате
        </span>
        <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Уточнить рекомендацию или разобрать вопрос отдельно
        </span>
      </div>
      <ArrowRight
        size={14}
        weight="regular"
        className="shrink-0 text-[color:var(--color-text-subtle)] transition-all group-hover:translate-x-0.5 group-hover:text-[color:var(--color-primary)]"
      />
    </Link>
  )
}

const PRIORITY_ORDER: Record<RecommendationPriority, number> = {
  high: 0,
  medium: 1,
  low: 2,
}

/**
 * Главная: hero-привет + summary профиля + топ-рекомендация большая +
 * остальные рекомендации компактно + CTA в чат.
 *
 * Состояния: loading (skeleton), error (можно повторить), empty
 * («ничего не нашлось — уточни цель»), normal.
 */
export default function HomePage() {
  // Узкий селектор — Home не ре-рендерится при правке полей профиля
  // (за это отвечает ProfileSummary, у него собственные подписки).
  const email = useAuthStore((s) => s.user?.email ?? null)
  const { data, isLoading, isError, refetch, isFetching } = useRecommendations()

  // Имя для приветствия — пока бэк не отдаёт full_name, берём префикс email.
  const greeting = email ? email.split('@')[0] : 'студент'

  // Сортировка по приоритету: high → medium → low.
  const sortedRecs = data
    ? [...data].sort(
        (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
      )
    : []
  const topRec = sortedRecs[0]
  const restRecs = sortedRecs.slice(1)

  return (
    <>
      <PageTopBar title="Главная" />
      <div className="mx-auto max-w-[1040px] px-[var(--space-2xl)] py-[var(--space-2xl)]">
        {/* Hero */}
        <section className="mb-[var(--space-3xl)] flex flex-col gap-[var(--space-md)]">
          <h1 className="font-serif text-[length:var(--text-2xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
            Привет, {greeting}
          </h1>
          <p className="text-[length:var(--text-md)] text-[color:var(--color-text-muted)]">
            Вот что я предлагаю сегодня.
          </p>
          <ProfileSummary />
        </section>

        {/* Recommendations */}
        {isLoading ? (
          <RecommendationsSkeleton />
        ) : isError ? (
          <EmptyState
            title="Не удалось получить рекомендации"
            description="Возможно, временные проблемы с сервером. Попробуй ещё раз через минуту."
            action={
              <Button
                variant="outline"
                onClick={() => {
                  void refetch()
                }}
                disabled={isFetching}
              >
                Попробовать ещё раз
              </Button>
            }
          />
        ) : !topRec ? (
          <EmptyState
            title="Пока ничего не нашлось"
            description="Уточни карьерную цель или добавь пройденные курсы — тогда система подберёт что-то конкретное."
            action={
              <Button asChild variant="outline">
                <Link to={routes.profile}>Открыть профиль</Link>
              </Button>
            }
          />
        ) : (
          /* Единый поток: featured-карточка (визуально заявляет «главное»)
             → компактный список остальных через divide-y → CTA-карточка в
             чат. Никаких eyebrow-заголовков «Главное сейчас» / «Ещё»: они
             дублировали приоритет, который и так виден в caption карточки. */
          <section className="flex flex-col">
            <RecommendationCard
              recommendation={topRec}
              linkTo={routes.recommendation(topRec.rule_id)}
              featured
            />

            {restRecs.length > 0 && (
              <div className="mt-[var(--space-2xl)] flex flex-col gap-[var(--space-sm)]">
                {restRecs.map((rec) => (
                  <RecommendationCard
                    key={rec.rule_id}
                    recommendation={rec}
                    linkTo={routes.recommendation(rec.rule_id)}
                  />
                ))}
              </div>
            )}

            <div
              className={
                restRecs.length > 0
                  ? 'mt-[var(--space-lg)]'
                  : 'mt-[var(--space-2xl)]'
              }
            >
              <ChatCTACard />
            </div>
          </section>
        )}
      </div>
    </>
  )
}

function RecommendationsSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      {[
        { titleW: 'w-3/4', textW: 'w-2/3' },
        { titleW: 'w-2/3', textW: 'w-1/2' },
        { titleW: 'w-3/4', textW: 'w-3/5' },
      ].map((w, i) => (
        <div
          key={i}
          className="flex flex-col gap-[var(--space-sm)] px-[var(--space-base)] py-[var(--space-base)]"
        >
          <Skeleton className="h-3 w-32" />
          <Skeleton className={`h-6 ${w.titleW}`} />
          <Skeleton className={`h-4 ${w.textW}`} />
        </div>
      ))}
    </div>
  )
}
