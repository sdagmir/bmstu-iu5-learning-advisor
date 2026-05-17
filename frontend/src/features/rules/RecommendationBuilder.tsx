import { useMemo } from 'react'
import { Controller, type UseFormReturn } from 'react-hook-form'
import { useQuery } from '@tanstack/react-query'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { adminCatalogApi } from '@/features/catalog/adminApi'
import {
  COMPETENCY_CATEGORY_LABELS,
  RECOMMENDATION_CATEGORY_LABELS,
  RECOMMENDATION_PRIORITY_LABELS,
} from '@/constants/enums'
import type { RuleFormValues } from './schema'

const CATEGORY_OPTIONS = [
  'ck_course',
  'technopark',
  'focus',
  'coursework',
  'warning',
  'strategy',
] as const

const PRIORITY_OPTIONS = ['high', 'medium', 'low'] as const

/**
 * Sentinel для опции «не выбрано» — Radix Select запрещает пустые value,
 * поэтому мапим '' ↔ NONE на границе компонента.
 */
const COMPETENCY_NONE = '__none__'

interface RecommendationBuilderProps {
  form: UseFormReturn<RuleFormValues>
  disabled?: boolean
}

/**
 * Конструктор шаблона рекомендации — заменил сырое JSON-textarea. Из 57 правил
 * в `rules_data.py` используется ровно 5 ключей, JSON-fallback не нужен.
 *
 * Раскладка: 2-колоночная (категория + приоритет) → заголовок → обоснование →
 * опциональный competency_gap (связь с радаром компетенций).
 */
export function RecommendationBuilder({ form, disabled = false }: RecommendationBuilderProps) {
  const errors = form.formState.errors.recommendation

  const competenciesQuery = useQuery({
    queryKey: ['admin', 'competencies'],
    queryFn: adminCatalogApi.competencies.list,
    staleTime: 60_000,
  })

  // Группируем компетенции по категории и сортируем внутри по имени —
  // в Select легче найти нужную (категории → потом имена).
  const groupedCompetencies = useMemo(() => {
    const list = competenciesQuery.data ?? []
    const byCategory = new Map<string, typeof list>()
    for (const c of list) {
      const arr = byCategory.get(c.category) ?? []
      arr.push(c)
      byCategory.set(c.category, arr)
    }
    return Array.from(byCategory.entries())
      .map(([cat, items]) => ({
        category: cat as keyof typeof COMPETENCY_CATEGORY_LABELS,
        items: [...items].sort((a, b) => a.name.localeCompare(b.name, 'ru')),
      }))
      .sort((a, b) =>
        COMPETENCY_CATEGORY_LABELS[a.category].localeCompare(
          COMPETENCY_CATEGORY_LABELS[b.category],
          'ru',
        ),
      )
  }, [competenciesQuery.data])

  return (
    <section className="flex flex-col gap-[var(--space-base)]">
      <header className="flex items-baseline justify-between gap-[var(--space-base)]">
        <h3 className="font-serif text-[length:var(--text-sm)] font-semibold tracking-tight text-[color:var(--color-text)]">
          Шаблон рекомендации
        </h3>
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
          то, что увидит студент, когда правило сработает
        </span>
      </header>

      <div className="grid grid-cols-[1fr_1fr] gap-[var(--space-base)]">
        <Field label="Категория" error={errors?.category?.message}>
          <Controller
            control={form.control}
            name="recommendation.category"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={disabled}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((c) => (
                    <SelectItem key={c} value={c}>
                      {RECOMMENDATION_CATEGORY_LABELS[c]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </Field>

        <Field label="Приоритет" error={errors?.priority?.message}>
          <Controller
            control={form.control}
            name="recommendation.priority"
            render={({ field }) => (
              <Select
                value={field.value}
                onValueChange={field.onChange}
                disabled={disabled}
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_OPTIONS.map((p) => (
                    <SelectItem key={p} value={p}>
                      {RECOMMENDATION_PRIORITY_LABELS[p]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </Field>
      </div>

      <Field label="Заголовок" error={errors?.title?.message}>
        <Input
          disabled={disabled}
          placeholder="Например: «Курс ЦК «Цифровые навыки»»"
          {...form.register('recommendation.title')}
        />
      </Field>

      <Field
        label="Обоснование"
        hint="одно-два предложения — почему именно эта рекомендация студенту"
        error={errors?.reasoning?.message}
      >
        <textarea
          rows={4}
          disabled={disabled}
          placeholder="На ранних семестрах при ещё не определённой карьерной цели первоочередной задачей…"
          {...form.register('recommendation.reasoning')}
          className="w-full resize-y rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
        />
      </Field>

      <Field
        label="Связь с компетенцией"
        hint="опционально · какую компетенцию из радара закрывает рекомендация"
        error={errors?.competencyGap?.message}
      >
        <Controller
          control={form.control}
          name="recommendation.competencyGap"
          render={({ field }) => (
            <Select
              value={field.value || COMPETENCY_NONE}
              onValueChange={(v) =>
                field.onChange(v === COMPETENCY_NONE ? '' : v)
              }
              disabled={disabled || competenciesQuery.isLoading}
            >
              <SelectTrigger size="sm" className="w-full">
                <SelectValue
                  placeholder={
                    competenciesQuery.isLoading
                      ? 'Загружаем компетенции…'
                      : 'Не выбрано'
                  }
                />
              </SelectTrigger>
              <SelectContent className="max-h-[320px]">
                <SelectItem value={COMPETENCY_NONE}>
                  <span className="text-[color:var(--color-text-muted)]">
                    Не выбрано
                  </span>
                </SelectItem>
                {groupedCompetencies.map(({ category, items }) => (
                  <div key={category}>
                    <div className="px-[var(--space-sm)] pt-[var(--space-sm)] pb-[var(--space-xs)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                      {COMPETENCY_CATEGORY_LABELS[category]}
                    </div>
                    {items.map((c) => (
                      <SelectItem key={c.id} value={c.tag}>
                        <span className="flex items-baseline gap-[var(--space-sm)]">
                          <span>{c.name}</span>
                          <span className="font-mono text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                            {c.tag}
                          </span>
                        </span>
                      </SelectItem>
                    ))}
                  </div>
                ))}
              </SelectContent>
            </Select>
          )}
        />
      </Field>
    </section>
  )
}

interface FieldProps {
  label: string
  hint?: string | undefined
  error?: string | undefined
  children: React.ReactNode
}

function Field({ label, hint, error, children }: FieldProps) {
  return (
    <div className="flex flex-col gap-[var(--space-xs)]">
      <div className="flex items-baseline justify-between gap-[var(--space-base)]">
        <Label className="text-[length:var(--text-sm)]">{label}</Label>
        {hint && (
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
            {hint}
          </span>
        )}
      </div>
      {children}
      {error && (
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
          {error}
        </span>
      )}
    </div>
  )
}
