import { useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Scales } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { EmptyState } from '@/components/common/EmptyState'
import { useRules, useRulePreview } from '@/features/rules/useRules'
import { useRuleLock } from '@/features/rules/useRuleLock'
import { RulesLockHeader } from '@/features/rules/RulesLockHeader'
import { RuleList } from '@/features/rules/RuleList'
import { RuleForm } from '@/features/rules/RuleForm'
import { SandboxPanel } from '@/features/rules/SandboxPanel'
import { PRESETS } from '@/features/simulator/presets'
import { usePersistentState } from '@/hooks/usePersistentState'
import type { RuleUpdate, SimulatorProfile } from '@/types/api'

const SELECTION_NEW = '__new__'

/**
 * Phase 7 — главная страница конструктора правил ЭС.
 *
 * 3-колоночный layout под admin-shell:
 *   [Список 360px] [Форма flex] [Sandbox 420px]
 * Все три колонки скроллятся независимо. Сверху — RulesLockHeader sticky.
 *
 * Выбранное правило хранится в URL (?ruleId=...), чтобы шаринг работал и
 * F5 не сбрасывал контекст. `?ruleId=__new__` — режим создания.
 */
export default function RulesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const ruleIdParam = searchParams.get('ruleId')
  const isNew = ruleIdParam === SELECTION_NEW

  const lock = useRuleLock()
  const { list, create, update, remove, publish, unpublish } = useRules()
  const previewMut = useRulePreview()

  const rules = list.data
  const selected = useMemo(
    () =>
      !isNew && ruleIdParam
        ? (rules?.find((r) => r.id === ruleIdParam) ?? null)
        : null,
    [rules, ruleIdParam, isNew],
  )

  // `number` уникален в БД, поэтому при создании предлагаем следующий свободный.
  const nextNumber = useMemo(
    () => (rules && rules.length > 0 ? Math.max(...rules.map((r) => r.number)) + 1 : 1),
    [rules],
  )

  // ── Sandbox profile state живёт здесь, persist в sessionStorage чтобы
  //    пережить навигацию между admin-экранами в одной вкладке. ──
  const [sandboxProfile, setSandboxProfile] = usePersistentState<SimulatorProfile>(
    'admin.rules.sandbox-profile',
    PRESETS[0]!.profile,
  )
  const updateProfile = (patch: Partial<SimulatorProfile>) =>
    setSandboxProfile((p) => ({ ...p, ...patch }))

  const previewResult = previewMut.data ?? null

  // При смене selected правила сбрасываем preview, чтобы чужой результат не путал.
  // Сам sandbox-профиль остаётся — он независим от того, что в форме.
  const previewReset = previewMut.reset
  useEffect(() => {
    previewReset()
  }, [ruleIdParam, previewReset])

  const selectRule = (id: string) => {
    setSearchParams({ ruleId: id }, { replace: true })
  }

  const startCreate = () => {
    setSearchParams({ ruleId: SELECTION_NEW }, { replace: true })
  }

  const runPreview = (includeDrafts: boolean) => {
    previewMut.mutate({ profile: sandboxProfile, include_drafts: includeDrafts })
  }

  const handleSaveUpdate = (id: string, body: RuleUpdate) =>
    update.mutate({ id, body })

  // После создания — переключаемся на новое правило по id из ответа.
  const createReset = create.reset
  useEffect(() => {
    if (create.isSuccess && create.data) {
      setSearchParams({ ruleId: create.data.id }, { replace: true })
      createReset()
    }
  }, [create.isSuccess, create.data, setSearchParams, createReset])

  // После удаления — снимаем выделение.
  const removeReset = remove.reset
  useEffect(() => {
    if (remove.isSuccess) {
      setSearchParams({}, { replace: true })
      removeReset()
    }
  }, [remove.isSuccess, setSearchParams, removeReset])

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageTopBar
        title="Правила ЭС"
        icon={<Scales size={18} weight="regular" />}
      />

      <RulesLockHeader
        status={lock.status}
        secondsLeft={lock.secondsLeft}
        isAcquiring={lock.isAcquiring}
        isReleasing={lock.isReleasing}
        isForceReleasing={lock.isForceReleasing}
        onAcquire={() => lock.acquire()}
        onRelease={() => lock.release()}
        onForceRelease={() => lock.forceRelease()}
      />

      <div className="grid min-h-0 flex-1 grid-cols-[360px_minmax(0,1fr)_420px] overflow-hidden">
        {/* Левая колонка — список правил */}
        <aside className="overflow-hidden border-r border-[color:var(--color-border)]">
          <RuleList
            rules={rules}
            isLoading={list.isLoading}
            selectedId={selected?.id ?? (isNew ? SELECTION_NEW : null)}
            canEdit={lock.canEdit}
            onSelect={selectRule}
            onCreate={startCreate}
          />
        </aside>

        {/* Центр — форма или плейсхолдер */}
        <main className="overflow-hidden">
          {selected || isNew ? (
            <RuleForm
              rule={selected}
              isNew={isNew}
              canEdit={lock.canEdit}
              isSaving={create.isPending || update.isPending}
              isPublishing={publish.isPending || unpublish.isPending}
              isDeleting={remove.isPending}
              nextNumber={nextNumber}
              onSaveCreate={create.mutate}
              onSaveUpdate={handleSaveUpdate}
              onPublishToggle={(id, currentlyPublished) => {
                if (currentlyPublished) unpublish.mutate(id)
                else publish.mutate(id)
              }}
              onDelete={remove.mutate}
              onAfterSave={() => runPreview(true)}
            />
          ) : (
            <div className="flex h-full items-center justify-center px-[var(--space-2xl)]">
              <EmptyState
                title="Выбери правило слева"
                description="…или нажми «Новое», чтобы создать с нуля. Условия редактируются JSON-ом, sandbox справа сразу покажет, что сработает."
              />
            </div>
          )}
        </main>

        {/* Правая колонка — sandbox preview */}
        <aside className="overflow-hidden border-l border-[color:var(--color-border)] bg-[color:var(--color-surface-muted)]">
          <SandboxPanel
            profile={sandboxProfile}
            onProfileChange={updateProfile}
            onProfileReplace={setSandboxProfile}
            result={previewResult}
            isPending={previewMut.isPending}
            rules={rules}
            onRun={runPreview}
            onSelectRule={selectRule}
          />
        </aside>
      </div>
    </div>
  )
}
