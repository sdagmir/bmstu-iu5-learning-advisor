import { CircleNotch, Lightning } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { RecommendationCard } from '@/features/recommendation/RecommendationCard'
import { ProfileInputForm } from '@/features/simulator/ProfileInputForm'
import { RulesTracePanel } from '@/features/simulator/RulesTracePanel'
import { useSimulator } from '@/features/simulator/useSimulator'
import { PRESETS } from '@/features/simulator/presets'
import { usePersistentState } from '@/hooks/usePersistentState'

const PLACEHOLDER_PRESET = '__custom__'

/**
 * Симулятор ЭС — admin-only «лаборатория» правил для демо защиты.
 *
 * 3-колоночный layout:
 *  - Слева (320px): форма X1–X12 + dropdown пресетов
 *  - Центр (flex): рекомендации Y1–Y6 в admin-режиме
 *  - Справа (380px): trace всех 52 правил с fired/skipped
 *
 * Любое изменение поля → debounced (250ms) /expert/evaluate/debug → весь
 * экран пересчитывается. Это и есть «магия прозрачна» — каждая
 * рекомендация привязана к конкретному правилу видимому в trace.
 */
export default function SimulatorPage() {
  const initial = PRESETS[0]!.profile
  const [activePresetId, setActivePresetId] = usePersistentState<string>(
    'admin.simulator.preset',
    PRESETS[0]!.id,
  )
  const { profile, update, replace, result, isPending } = useSimulator(initial)

  const onPresetChange = (id: string) => {
    if (id === PLACEHOLDER_PRESET) return
    const preset = PRESETS.find((p) => p.id === id)
    if (!preset) return
    setActivePresetId(id)
    replace(preset.profile)
  }

  // Если поля менялись вручную после загрузки пресета — снимаем active.
  const onFieldChange = (patch: Parameters<typeof update>[0]) => {
    setActivePresetId(PLACEHOLDER_PRESET)
    update(patch)
  }

  const recommendations = result?.recommendations ?? []
  const trace = result?.trace ?? null

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageTopBar
        title="Симулятор ЭС"
        icon={<Lightning size={18} weight="regular" />}
        actions={
          isPending ? (
            <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
              <CircleNotch size={14} weight="regular" className="animate-spin" />
              Считаем
            </span>
          ) : null
        }
      />
      <div className="grid min-h-0 flex-1 grid-cols-[320px_1fr_380px] overflow-hidden">
        {/* Левая колонка: форма + пресеты */}
        <aside className="flex flex-col gap-[var(--space-lg)] overflow-y-auto border-r border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-lg)]">
          <div className="flex flex-col gap-[var(--space-xs)]">
            <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
              Пресет
            </span>
            <Select value={activePresetId} onValueChange={onPresetChange}>
              <SelectTrigger size="sm" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {activePresetId === PLACEHOLDER_PRESET && (
                  <SelectItem value={PLACEHOLDER_PRESET}>Кастомный профиль</SelectItem>
                )}
                {PRESETS.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <ProfileInputForm profile={profile} onChange={onFieldChange} />
        </aside>

        {/* Центр: рекомендации */}
        <main className="overflow-y-auto px-[var(--space-2xl)] py-[var(--space-lg)]">
          <div className="flex flex-col gap-[var(--space-xs)] pb-[var(--space-base)]">
            <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
              Рекомендации
            </span>
            <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)] tabular-nums">
              {recommendations.length} {recommendations.length === 1 ? 'результат' : 'результатов'}
            </span>
          </div>

          {recommendations.length === 0 ? (
            <div className="py-[var(--space-2xl)] text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
              {result === null
                ? 'Заполни профиль слева — справа появятся рекомендации и trace.'
                : 'Ни одно правило не сработало для этого профиля.'}
            </div>
          ) : (
            <div className="flex flex-col">
              {recommendations.map((rec) => (
                <RecommendationCard key={rec.rule_id} recommendation={rec} mode="admin" />
              ))}
            </div>
          )}
        </main>

        {/* Правая: trace */}
        <aside className="overflow-y-auto border-l border-[color:var(--color-border)] bg-[color:var(--color-surface-muted)] px-[var(--space-base)] py-[var(--space-lg)]">
          <RulesTracePanel
            entries={trace?.entries ?? null}
            totalChecked={trace?.total_checked ?? 52}
            totalFired={trace?.total_fired ?? 0}
          />
        </aside>
      </div>
    </div>
  )
}
