import { Lightning } from '@phosphor-icons/react'
import { cn } from '@/lib/utils'
import type { Rule } from '@/types/api'

interface FiredRulesListProps {
  firedRuleIds: string[]
  totalChecked: number
  rules: Rule[] | undefined
  onSelect: (id: string) => void
}

/**
 * Список правил, сработавших на preview. Каждая строка — кликабельный
 * R-ключ + название (truncate). Клик — навигация в RuleList слева.
 *
 * `firedRuleIds` приходят с бэка как строки `"R12"` (поле rule_key
 * движка). Мапим на актуальные правила из списка по `number`.
 */
export function FiredRulesList({
  firedRuleIds,
  totalChecked,
  rules,
  onSelect,
}: FiredRulesListProps) {
  const matched = firedRuleIds
    .map((rid) => {
      const num = parseRuleNumber(rid)
      const rule = rules?.find((r) => r.number === num)
      return { rid, num, rule }
    })

  return (
    <div className="flex flex-col gap-[var(--space-sm)]">
      <div className="flex items-baseline justify-between">
        <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          Сработало
        </span>
        <span className="text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-muted)]">
          {firedRuleIds.length} из {totalChecked}
        </span>
      </div>

      {matched.length === 0 ? (
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
          Ни одно правило не сработало для этого профиля.
        </p>
      ) : (
        <ul className="flex flex-col">
          {matched.map(({ rid, rule }) => (
            <li key={rid}>
              <button
                type="button"
                disabled={!rule}
                onClick={() => rule && onSelect(rule.id)}
                className={cn(
                  'flex w-full items-center gap-[var(--space-sm)] rounded-[6px] px-[var(--space-sm)] py-[var(--space-xs)] text-left transition-colors',
                  rule
                    ? 'hover:bg-[color:var(--color-surface-hover)]'
                    : 'cursor-not-allowed opacity-60',
                )}
              >
                <Lightning
                  size={12}
                  weight="regular"
                  className="shrink-0 text-[color:var(--color-text-subtle)]"
                />
                <span className="font-mono text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-primary)]">
                  {rid}
                </span>
                <span className="line-clamp-1 text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
                  {rule?.name ?? 'правило не найдено'}
                </span>
                {rule && !rule.is_published && (
                  <span className="ml-auto rounded-[3px] border border-[color:var(--color-border)] px-[var(--space-xs)] py-[1px] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                    draft
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** `R-017` / `R17` / `R 17` → 17 (или NaN — тогда не свяжется). */
function parseRuleNumber(rid: string): number {
  const m = rid.match(/(\d+)/)
  return m ? Number(m[1]) : Number.NaN
}
