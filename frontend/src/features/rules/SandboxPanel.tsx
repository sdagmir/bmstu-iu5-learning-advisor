import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { usePersistentState } from '@/hooks/usePersistentState'
import {
  CaretDown,
  CaretUp,
  CircleNotch,
  Play,
  CheckCircle,
} from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ProfileInputForm } from '@/features/simulator/ProfileInputForm'
import { PRESETS } from '@/features/simulator/presets'
import { RecommendationCard } from '@/features/recommendation/RecommendationCard'
import { adminCatalogApi } from '@/features/catalog/adminApi'
import { FiredRulesList } from './FiredRulesList'
import { cn } from '@/lib/utils'
import type { Rule, RulePreviewResponse, SimulatorProfile } from '@/types/api'

interface SandboxPanelProps {
  profile: SimulatorProfile
  onProfileChange: (patch: Partial<SimulatorProfile>) => void
  onProfileReplace: (next: SimulatorProfile) => void
  result: RulePreviewResponse | null
  isPending: boolean
  rules: Rule[] | undefined
  onRun: (includeDrafts: boolean) => void
  onSelectRule: (id: string) => void
}

const PLACEHOLDER_PRESET = '__custom__'
const STUDENT_PLACEHOLDER = '__none__'

/**
 * Правая колонка RulesPage. Всегда видна, чтобы редактор не делал «вход в
 * симулятор и обратно». В отличие от Simulator (Phase 8) — без debounce-
 * пересчёта на каждое изменение поля: эксперт явно жмёт «прогнать», иначе
 * на сложных правилах накопится много preview-вызовов.
 */
export function SandboxPanel({
  profile,
  onProfileChange,
  onProfileReplace,
  result,
  isPending,
  rules,
  onRun,
  onSelectRule,
}: SandboxPanelProps) {
  const [formCollapsed, setFormCollapsed] = useState(false)
  // Preset persist'им в sessionStorage в паре с профилем (см. RulesPage),
  // чтобы dropdown показывал тот же выбор после возврата на экран.
  const [preset, setPreset] = usePersistentState<string>(
    'admin.rules.sandbox-preset',
    PLACEHOLDER_PRESET,
  )

  // Список студентов для «загрузить из студента» — лениво, по факту
  // открытия Sandbox-экрана. Кэш TanStack бережёт от повторных запросов.
  const usersQuery = useQuery({
    queryKey: ['admin', 'users', 'sandbox'],
    queryFn: adminCatalogApi.users.list,
    staleTime: 60_000,
  })
  const students = (usersQuery.data ?? []).filter((u) => u.role === 'student')
  // Selected student хранится отдельно от loading-флага: после успешной
  // загрузки Select продолжает показывать email — эксперт видит, что
  // профиль явно загружен «из X», а не сорвался обратно в плейсхолдер.
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null)
  const [loadingStudentId, setLoadingStudentId] = useState<string | null>(null)

  const onPresetChange = (id: string) => {
    if (id === PLACEHOLDER_PRESET) return
    const p = PRESETS.find((x) => x.id === id)
    if (!p) return
    setPreset(id)
    setSelectedStudentId(null)
    onProfileReplace(p.profile)
  }

  const onStudentSelect = async (id: string) => {
    if (id === STUDENT_PLACEHOLDER) return
    setLoadingStudentId(id)
    try {
      const snapshot = await adminCatalogApi.users.profileSnapshot(id)
      onProfileReplace(snapshot)
      setPreset(PLACEHOLDER_PRESET)
      setSelectedStudentId(id)
    } catch (err) {
      toast.error(
        err instanceof Error
          ? err.message
          : 'Не удалось загрузить профиль студента',
      )
    } finally {
      setLoadingStudentId(null)
    }
  }

  const handleProfileChange = (patch: Partial<SimulatorProfile>) => {
    setPreset(PLACEHOLDER_PRESET)
    setSelectedStudentId(null)
    onProfileChange(patch)
  }

  const selectedStudentEmail = selectedStudentId
    ? students.find((s) => s.id === selectedStudentId)?.email ?? null
    : null

  return (
    <div className="flex h-full min-w-0 flex-col">
      <div className="flex items-center justify-between gap-[var(--space-base)] border-b border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-md)]">
        <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          Sandbox
        </span>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setFormCollapsed((v) => !v)}
              aria-label={formCollapsed ? 'Развернуть форму' : 'Свернуть форму'}
            >
              {formCollapsed ? <CaretDown size={14} /> : <CaretUp size={14} />}
              {formCollapsed ? 'Развернуть' : 'Свернуть форму'}
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            {formCollapsed
              ? 'Снова показать форму X1–X12'
              : 'Освободить место под рекомендации'}
          </TooltipContent>
        </Tooltip>
      </div>

      <div className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto px-[var(--space-base)] py-[var(--space-base)]">
        {!formCollapsed && (
          <div className="mb-[var(--space-lg)] flex flex-col gap-[var(--space-base)]">
            <div className="flex flex-col gap-[var(--space-xs)]">
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                Пресет профиля
              </span>
              <Select value={preset} onValueChange={onPresetChange}>
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue placeholder="Выбрать готовый профиль…" />
                </SelectTrigger>
                <SelectContent>
                  {preset === PLACEHOLDER_PRESET && (
                    <SelectItem value={PLACEHOLDER_PRESET}>
                      Кастомный профиль
                    </SelectItem>
                  )}
                  {PRESETS.map((p) => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-col gap-[var(--space-xs)]">
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                Загрузить из студента
              </span>
              <Select
                value={selectedStudentId ?? STUDENT_PLACEHOLDER}
                onValueChange={onStudentSelect}
                disabled={
                  usersQuery.isLoading ||
                  loadingStudentId !== null ||
                  students.length === 0
                }
              >
                <SelectTrigger size="sm" className="w-full">
                  <SelectValue
                    placeholder={
                      usersQuery.isLoading
                        ? 'Загружаем…'
                        : students.length === 0
                          ? 'Нет студентов в БД'
                          : 'Выбрать студента по email…'
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {students.map((s) => (
                    <SelectItem key={s.id} value={s.id}>
                      {s.email}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {loadingStudentId ? (
                <span className="flex items-center gap-[var(--space-xs)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                  <CircleNotch size={12} className="animate-spin" /> Подтягиваем
                  X1–X12 студента…
                </span>
              ) : (
                selectedStudentEmail && (
                  <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                    Профиль загружен из {selectedStudentEmail}
                  </span>
                )
              )}
            </div>

            <ProfileInputForm profile={profile} onChange={handleProfileChange} />
          </div>
        )}

        <div className="flex flex-col gap-[var(--space-sm)]">
          <div className="flex flex-col gap-[var(--space-xs)]">
            <Button
              size="sm"
              onClick={() => onRun(true)}
              disabled={isPending}
              className="w-full"
            >
              {isPending ? (
                <CircleNotch size={14} className="animate-spin" />
              ) : (
                <Play size={14} weight="fill" />
              )}
              Прогнать с черновиками
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onRun(false)}
              disabled={isPending}
              className="w-full"
            >
              <CheckCircle size={14} weight="regular" />
              Только опубликованные
            </Button>
          </div>
          <p className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            preview не влияет на студентов и не требует захвата лока
          </p>
        </div>

        <div className="my-[var(--space-lg)] h-px bg-[color:var(--color-border)]" />

        {result ? (
          <div className="flex flex-col gap-[var(--space-lg)]">
            <FiredRulesList
              firedRuleIds={result.fired_rule_ids}
              totalChecked={result.total_checked}
              rules={rules}
              onSelect={onSelectRule}
            />

            <div
              className={cn(
                'flex flex-col gap-[var(--space-sm)]',
                isPending && 'opacity-50',
              )}
            >
              <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
                Рекомендации · {result.recommendations.length}
              </span>
              {result.recommendations.length === 0 ? (
                <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
                  ЭС не выдала ни одной рекомендации.
                </p>
              ) : (
                <div className="flex flex-col gap-[var(--space-xs)]">
                  {result.recommendations.map((rec) => {
                    // rec.rule_id формата "R12" → находим Rule по number,
                    // чтобы прокинуть trigger_count в admin-карточку
                    const num = Number((rec.rule_id.match(/\d+/) ?? [])[0])
                    const rule = rules?.find((r) => r.number === num)
                    return (
                      <RecommendationCard
                        key={rec.rule_id}
                        recommendation={rec}
                        mode="admin"
                        triggerCount={rule?.trigger_count ?? 0}
                        onRuleClick={(rid) => {
                          const n = Number((rid.match(/\d+/) ?? [])[0])
                          const r = rules?.find((x) => x.number === n)
                          if (r) onSelectRule(r.id)
                        }}
                      />
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        ) : (
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
            Заполни профиль и нажми «Прогнать» — увидишь, какие правила
            сработают и что выдаст ЭС.
          </p>
        )}
      </div>
    </div>
  )
}
