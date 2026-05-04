import { memo, useMemo, useState } from 'react'
import { Plus, MagnifyingGlass } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Skeleton } from '@/components/ui/skeleton'
import { RuleStatusBadge } from './RuleStatusBadge'
import { RULE_GROUP_LABELS } from '@/constants/enums'
import { cn } from '@/lib/utils'
import type { Rule } from '@/types/api'

type StatusFilter = 'all' | 'published' | 'draft' | 'inactive'

interface RuleListProps {
  rules: Rule[] | undefined
  isLoading: boolean
  selectedId: string | null
  canEdit: boolean
  onSelect: (id: string) => void
  onCreate: () => void
}

const FILTER_LABELS: Record<StatusFilter, string> = {
  all: 'Все правила',
  published: 'Только опубликованные',
  draft: 'Только черновики',
  inactive: 'Опубликованные · выключенные',
}

/**
 * Левая колонка RulesPage. Плотный список с поиском и фильтром по статусу.
 * Узкая колонка ≈ 360px — поэтому без таблицы; одна строка = одна строка.
 *
 * Активная строка — фон `--color-primary-soft`, без левой полоски (запрет
 * side-stripe). Hover на остальных — `--color-surface-hover`.
 */
export function RuleList({
  rules,
  isLoading,
  selectedId,
  canEdit,
  onSelect,
  onCreate,
}: RuleListProps) {
  const [filter, setFilter] = useState<StatusFilter>('all')
  const [query, setQuery] = useState('')

  const visible = useMemo(() => {
    if (!rules) return []
    const q = query.trim().toLowerCase()
    return rules
      .filter((r) => {
        if (filter === 'published') return r.is_published
        if (filter === 'draft') return !r.is_published
        if (filter === 'inactive') return r.is_published && !r.is_active
        return true
      })
      .filter((r) => {
        if (!q) return true
        return (
          r.name.toLowerCase().includes(q) ||
          `r${r.number}`.includes(q) ||
          `r-${r.number}`.includes(q) ||
          RULE_GROUP_LABELS[r.group].toLowerCase().includes(q)
        )
      })
      .sort((a, b) => a.number - b.number)
  }, [rules, filter, query])

  return (
    <div className="flex h-full flex-col">
      <div className="flex flex-col gap-[var(--space-sm)] border-b border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-md)]">
        <div className="flex items-center justify-between gap-[var(--space-sm)]">
          <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
            Правила {rules ? `· ${rules.length}` : ''}
          </span>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                size="sm"
                onClick={onCreate}
                disabled={!canEdit}
                aria-label="Создать новое правило"
              >
                <Plus size={14} weight="bold" />
                Новое
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {canEdit ? 'Создать новое правило' : 'Сначала войди в редактор'}
            </TooltipContent>
          </Tooltip>
        </div>

        <div className="relative">
          <MagnifyingGlass
            size={14}
            className="pointer-events-none absolute top-1/2 left-[var(--space-sm)] -translate-y-1/2 text-[color:var(--color-text-subtle)]"
          />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Поиск: R-17, ML, Технопарк…"
            className="h-8 pl-[calc(var(--space-sm)+1.25rem)] text-[length:var(--text-sm)]"
          />
        </div>

        <Select value={filter} onValueChange={(v) => setFilter(v as StatusFilter)}>
          <SelectTrigger size="sm" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {(Object.keys(FILTER_LABELS) as StatusFilter[]).map((f) => (
              <SelectItem key={f} value={f}>
                {FILTER_LABELS[f]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <ListSkeleton />
        ) : visible.length === 0 ? (
          <div className="px-[var(--space-base)] py-[var(--space-2xl)] text-center text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
            {rules && rules.length === 0
              ? 'Пока нет правил. Создай первое.'
              : 'Ничего не нашлось'}
          </div>
        ) : (
          <div className="flex flex-col">
            {visible.map((rule) => (
              <RuleRow
                key={rule.id}
                rule={rule}
                isSelected={rule.id === selectedId}
                onSelect={onSelect}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

interface RuleRowProps {
  rule: Rule
  isSelected: boolean
  onSelect: (id: string) => void
}

const RuleRow = memo(function RuleRow({ rule, isSelected, onSelect }: RuleRowProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(rule.id)}
      aria-current={isSelected ? 'true' : undefined}
      className={cn(
        'flex flex-col items-start gap-[2px] px-[var(--space-base)] py-[var(--space-sm)] text-left transition-colors',
        isSelected
          ? 'bg-[color:var(--color-primary-soft)]'
          : 'hover:bg-[color:var(--color-surface-hover)]',
      )}
    >
      <div className="flex w-full items-center gap-[var(--space-sm)]">
        <span className="font-mono text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-muted)]">
          R-{String(rule.number).padStart(3, '0')}
        </span>
        <span className="ml-auto">
          <RuleStatusBadge isPublished={rule.is_published} isActive={rule.is_active} />
        </span>
      </div>
      <span
        className={cn(
          'line-clamp-1 text-[length:var(--text-sm)]',
          isSelected
            ? 'font-medium text-[color:var(--color-primary)]'
            : 'text-[color:var(--color-text)]',
        )}
      >
        {rule.name}
      </span>
      <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
        {RULE_GROUP_LABELS[rule.group]}
      </span>
    </button>
  )
})

function ListSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--space-xs)] p-[var(--space-base)]">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex flex-col gap-[var(--space-xs)]">
          <div className="flex items-center gap-[var(--space-sm)]">
            <Skeleton className="h-3 w-12" />
            <Skeleton className="ml-auto h-4 w-20" />
          </div>
          <Skeleton
            className="h-3"
            style={{ width: `${50 + ((i * 7) % 40)}%` }}
          />
        </div>
      ))}
    </div>
  )
}
