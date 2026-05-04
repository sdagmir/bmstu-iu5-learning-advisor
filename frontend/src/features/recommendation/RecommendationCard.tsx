import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CaretDown } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import type { Recommendation } from '@/types/api'
import {
  RECOMMENDATION_CATEGORY_LABELS,
  RECOMMENDATION_PRIORITY_LABELS,
} from '@/constants/enums'

export interface RelatedCompetency {
  id: string
  name: string
}

interface RecommendationCardProps {
  recommendation: Recommendation
  /** `user` — человеческий копи; `admin` — добавляет rule_id и trigger-counter. */
  mode?: 'user' | 'admin'
  /** Кол-во срабатываний правила. Только в admin-mode. */
  triggerCount?: number
  /** Callback на клик по rule_id (вести в симулятор). Только в admin-mode. */
  onRuleClick?: (ruleId: string) => void
  /** Связанные компетенции — chips в expanded-секции. */
  relatedCompetencies?: RelatedCompetency[]
  /** Если задан — title рендерится как ссылка на детальную страницу. */
  linkTo?: string
}

/**
 * Hero-компонент продукта. Одна карточка = одна рекомендация (Y1–Y6).
 *
 * Дизайн-принципы (per .impeccable.md + design-brief):
 * - Никаких цветных блоков-подложек за карточкой. Разделение от соседних —
 *   только пустым пространством. Никаких side-stripe бордеров.
 * - Hover: едва заметный фон `--color-surface-muted`, без shadow и lift.
 * - Иерархия через типографику: caption → Bitter title → reasoning → meta tail.
 * - В expanded-секции: полный reasoning + chips компетенций.
 * - В admin-режиме: rule_id моноспейсом + счётчик срабатываний.
 */
export function RecommendationCard({
  recommendation,
  mode = 'user',
  triggerCount,
  onRuleClick,
  relatedCompetencies,
  linkTo,
}: RecommendationCardProps) {
  const [expanded, setExpanded] = useState(false)

  const categoryLabel = RECOMMENDATION_CATEGORY_LABELS[recommendation.category]
  const priorityLabel = RECOMMENDATION_PRIORITY_LABELS[recommendation.priority]

  // Раскрытие что-то даёт только если: reasoning потенциально обрезан
  // line-clamp-2 (эвристика: >120 символов) ИЛИ переданы relatedCompetencies.
  // Иначе кнопка «Подробнее» — пустышка, скрываем.
  const hasMoreContent =
    recommendation.reasoning.length > 120 ||
    (relatedCompetencies !== undefined && relatedCompetencies.length > 0)

  return (
    <article className="group flex flex-col gap-[var(--space-sm)] rounded-[6px] px-[var(--space-base)] py-[var(--space-base)] transition-colors hover:bg-[color:var(--color-surface-muted)]">
      {/* Caption: категория · приоритет (admin: + rule_id справа) */}
      <div className="flex items-center justify-between gap-[var(--space-base)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
        <span className="truncate">
          {categoryLabel} · {priorityLabel}
        </span>
        {mode === 'admin' && (
          <button
            type="button"
            onClick={() => onRuleClick?.(recommendation.rule_id)}
            className="shrink-0 cursor-pointer font-mono text-[length:var(--text-xs)] text-[color:var(--color-text-muted)] transition-colors hover:text-[color:var(--color-primary)]"
            aria-label={`Открыть правило ${recommendation.rule_id} в симуляторе`}
          >
            {recommendation.rule_id}
          </button>
        )}
      </div>

      {/* Title (Link если задан linkTo) */}
      <h3 className="font-serif text-[length:var(--text-lg)] font-semibold tracking-tight text-[color:var(--color-text)]">
        {linkTo ? (
          <Link
            to={linkTo}
            className="underline-offset-4 transition-colors hover:text-[color:var(--color-primary)] hover:underline focus-visible:underline"
          >
            {recommendation.title}
          </Link>
        ) : (
          recommendation.title
        )}
      </h3>

      {/* Reasoning snippet — line-clamp-2 в свёрнутом, full в раскрытом */}
      <p
        className={cn(
          'text-[length:var(--text-base)] leading-relaxed text-[color:var(--color-text-muted)]',
          !expanded && 'line-clamp-2',
        )}
      >
        {recommendation.reasoning}
      </p>

      {/* Meta tail — admin-only.
         В user-режиме `competency_gap` бесполезен: это сырой UID компетенции
         (например `ml_basics`), а человеческое имя сюда не приходит. Бренд:
         monospace ID — только в админке. Закрытые компетенции у студента
         отображаются на /coverage. */}
      {mode === 'admin' &&
        (recommendation.competency_gap || triggerCount !== undefined) && (
          <div className="flex flex-wrap items-center gap-[var(--space-xs)] text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-subtle)]">
            {recommendation.competency_gap && (
              <span>
                закрывает:{' '}
                <span className="font-mono">{recommendation.competency_gap}</span>
              </span>
            )}
            {triggerCount !== undefined && (
              <>
                {recommendation.competency_gap && <span aria-hidden>·</span>}
                <span>сработало {triggerCount}×</span>
              </>
            )}
          </div>
        )}

      {/* Disclosure — показываем ТОЛЬКО когда есть что развернуть. Иначе
         кнопка ничего не делала бы и сбивала с толку. */}
      {hasMoreContent && (
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          className="mt-[var(--space-xs)] flex w-fit cursor-pointer items-center gap-[var(--space-xs)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)] transition-colors hover:text-[color:var(--color-primary)]"
        >
          <CaretDown
            size={12}
            weight="bold"
            className={cn('transition-transform duration-150', expanded && 'rotate-180')}
          />
          {expanded ? 'Свернуть' : 'Подробнее'}
        </button>
      )}

      {/* Expanded section */}
      {expanded && hasMoreContent && (
        <div className="mt-[var(--space-sm)] flex flex-col gap-[var(--space-base)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
          {relatedCompetencies && relatedCompetencies.length > 0 && (
            <div className="flex flex-col gap-[var(--space-xs)]">
              <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                Связанные компетенции
              </span>
              <div className="flex flex-wrap gap-[var(--space-xs)]">
                {relatedCompetencies.map((c) => (
                  <span
                    key={c.id}
                    className="rounded-[4px] bg-[color:var(--color-surface-muted)] px-[var(--space-sm)] py-[2px] text-[length:var(--text-xs)] text-[color:var(--color-text)]"
                  >
                    {c.name}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </article>
  )
}
