import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { FloppyDisk, Eye, Trash, CircleNotch, EyeSlash, Code, Sliders } from '@phosphor-icons/react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { RuleStatusBadge } from './RuleStatusBadge'
import { JsonField } from './JsonField'
import { RecommendationBuilder } from './RecommendationBuilder'
import { ConditionBuilder } from './ConditionBuilder'
import {
  jsonToTree,
  newEmptyAllGroup,
  treeToJson,
  type GroupNode,
} from './conditionTree'
import {
  NEW_RULE_DEFAULTS,
  PRIORITY_LEVELS,
  buildRecommendation,
  parseJsonObject,
  parseRecommendation,
  priorityToBucket,
  ruleFormSchema,
  stringifyJson,
  type RuleFormValues,
} from './schema'
import { ALL_RULE_GROUPS, RULE_GROUP_LABELS } from '@/constants/enums'
import type { Rule, RuleCreate, RuleUpdate } from '@/types/api'

/**
 * Парсит conditionJson и пытается превратить в дерево для builder'а.
 * Возвращает {tree, fallback} — fallback=true если не получилось (lookup_*,
 * unknown param, кривой JSON) → RuleForm включит JSON-режим.
 */
function deriveTree(
  conditionJson: string,
): { tree: GroupNode; fallback: false } | { tree: null; fallback: true } {
  try {
    const parsed = JSON.parse(conditionJson)
    const node = jsonToTree(parsed)
    if (!node) return { tree: null, fallback: true }
    // Атом без group-обёртки — оборачиваем в all, чтобы builder всегда работал с группой
    const tree: GroupNode =
      node.kind === 'group'
        ? node
        : { kind: 'group', combinator: 'all', children: [node] }
    return { tree, fallback: false }
  } catch {
    return { tree: null, fallback: true }
  }
}

interface RuleFormProps {
  /** `null` — создание; объект — редактирование. */
  rule: Rule | null
  isNew: boolean
  canEdit: boolean
  isSaving: boolean
  isPublishing: boolean
  isDeleting: boolean
  /** Дефолт для номера при создании — `max(existing.number) + 1`. */
  nextNumber: number
  /** Возвращают Promise — submit ждёт коммита перед afterSave. */
  onSaveCreate: (body: RuleCreate) => Promise<unknown>
  onSaveUpdate: (id: string, body: RuleUpdate) => Promise<unknown>
  onPublishToggle: (id: string, currentlyPublished: boolean) => void
  onDelete: (id: string) => void
  /** Колбек после успешного сохранения — RulesPage запускает sandbox preview. */
  onAfterSave?: () => void
}

/** Преобразует `Rule` из бэка в значения формы. */
function ruleToValues(rule: Rule): RuleFormValues {
  return {
    number: rule.number,
    group: rule.group,
    name: rule.name,
    description: rule.description,
    conditionJson: stringifyJson(rule.condition),
    recommendation: parseRecommendation(rule.recommendation),
    // Legacy: в БД priority — произвольный int, округляем к ближайшему bucket
    // из 5 уровней. Раньше все правила имели priority=0 → станут «Минимальный».
    priority: priorityToBucket(rule.priority),
    is_active: rule.is_active,
  }
}

/**
 * Центральная колонка RulesPage. Save-only (без auto-save), потому что
 * правило публикуется атомарно и черновики могут быть в полу-валидном виде.
 *
 * Хот-кеи:
 *  - ⌘/Ctrl+S → save (если форма валидна и canEdit)
 *  - ⌘/Ctrl+Enter → save + триггер `onAfterSave` (RulesPage запускает preview)
 */
export function RuleForm({
  rule,
  isNew,
  canEdit,
  isSaving,
  isPublishing,
  isDeleting,
  nextNumber,
  onSaveCreate,
  onSaveUpdate,
  onPublishToggle,
  onDelete,
  onAfterSave,
}: RuleFormProps) {
  const [confirmDelete, setConfirmDelete] = useState(false)

  const form = useForm<RuleFormValues>({
    resolver: zodResolver(ruleFormSchema),
    defaultValues:
      isNew || !rule
        ? { ...NEW_RULE_DEFAULTS, number: nextNumber }
        : ruleToValues(rule),
    mode: 'onBlur',
  })

  // ── Condition builder mode ────────────────────────────────────────────
  // simple — визуальный конструктор; json — fallback для экзотики (lookup_*).
  // Source of truth — form.conditionJson (string). tree — derived view над ним.
  const initialDerive = deriveTree(form.getValues('conditionJson'))
  const [conditionMode, setConditionMode] = useState<'simple' | 'json'>(
    initialDerive.fallback ? 'json' : 'simple',
  )
  const [tree, setTree] = useState<GroupNode>(
    initialDerive.fallback ? newEmptyAllGroup() : initialDerive.tree,
  )

  // Перезагружаем форму + builder-tree при смене правила или выходе из new.
  // setState внутри effect здесь — легитимная синхронизация state с props
  // (правило в URL изменилось → нужно пересобрать форму).
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    const defaults =
      isNew || !rule
        ? { ...NEW_RULE_DEFAULTS, number: nextNumber }
        : ruleToValues(rule)
    form.reset(defaults)
    const derived = deriveTree(defaults.conditionJson)
    if (derived.fallback) {
      setTree(newEmptyAllGroup())
      setConditionMode('json')
    } else {
      setTree(derived.tree)
      setConditionMode('simple')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rule?.id, isNew, nextNumber])
  /* eslint-enable react-hooks/set-state-in-effect */

  // Builder → form: при изменении дерева пишем сериализованный JSON в форму.
  const handleTreeChange = (next: GroupNode) => {
    setTree(next)
    form.setValue('conditionJson', JSON.stringify(treeToJson(next), null, 2), {
      shouldDirty: true,
      shouldValidate: true,
    })
  }

  // Toggle mode. simple→json — просто переключаем. json→simple — пробуем парсить.
  const toggleConditionMode = () => {
    if (conditionMode === 'simple') {
      setConditionMode('json')
      return
    }
    const derived = deriveTree(form.getValues('conditionJson'))
    if (derived.fallback) {
      toast.error(
        'Условие содержит то, что конструктор пока не поддерживает (lookup_*, неизвестный параметр или невалидный JSON). Поправь JSON и попробуй снова.',
      )
      return
    }
    setTree(derived.tree)
    setConditionMode('simple')
  }

  const submit = (afterSave?: () => void) =>
    form.handleSubmit(async (values) => {
      let condition: Record<string, unknown>
      try {
        condition = parseJsonObject(values.conditionJson)
      } catch (e) {
        form.setError('conditionJson', {
          message: 'JSON не парсится: ' + (e as Error).message,
        })
        return
      }
      const recommendation = buildRecommendation(values.recommendation)
      try {
        if (isNew || !rule) {
          await onSaveCreate({
            number: values.number,
            group: values.group,
            name: values.name,
            description: values.description,
            condition,
            recommendation,
            priority: values.priority,
            is_active: values.is_active,
          })
        } else {
          await onSaveUpdate(rule.id, {
            group: values.group,
            name: values.name,
            description: values.description,
            condition,
            recommendation,
            priority: values.priority,
            is_active: values.is_active,
          })
        }
        afterSave?.()
      } catch {
        // toast.error уже показал useRules.onError; preview не запускаем.
      }
    })

  // ⌘S и ⌘Enter — обрабатываем на уровне <form>, чтобы фокус мог быть в любом поле.
  const onKeyDown = (e: React.KeyboardEvent<HTMLFormElement>) => {
    const meta = e.metaKey || e.ctrlKey
    if (!meta) return
    if (e.key === 's') {
      e.preventDefault()
      if (!canEdit || isSaving) return
      submit()()
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (!canEdit || isSaving) return
      submit(onAfterSave)()
    }
  }

  const isPublished = rule?.is_published ?? false
  const dirty = form.formState.isDirty
  const errors = form.formState.errors

  return (
    <form
      onSubmit={(e) => e.preventDefault()}
      onKeyDown={onKeyDown}
      className="flex h-full min-h-0 flex-col"
    >
      {/* ── Шапка ─────────────────────────────────────────────────────── */}
      <div className="flex items-center gap-[var(--space-base)] border-b border-[color:var(--color-border)] bg-[color:var(--color-bg)] px-[var(--space-2xl)] py-[var(--space-md)]">
        <div className="flex items-center gap-[var(--space-sm)]">
          <span className="font-mono text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
            {isNew || !rule ? 'R-новое' : `R-${String(rule.number).padStart(3, '0')}`}
          </span>
          {rule && !isNew && (
            <RuleStatusBadge isPublished={rule.is_published} isActive={rule.is_active} />
          )}
        </div>
        {!isNew && rule && (
          <label className="ml-auto flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            <span>Активно</span>
            <Controller
              control={form.control}
              name="is_active"
              render={({ field }) => (
                <Switch
                  checked={field.value}
                  onCheckedChange={field.onChange}
                  disabled={!canEdit}
                />
              )}
            />
          </label>
        )}
      </div>

      {/* ── Скроллируемое тело ──────────────────────────────────────────
         min-h-0 ОБЯЗАТЕЛЕН: без него flex-1 не ужимается ниже intrinsic
         content и body «продавливает» admin-shell main, появляется window
         scrollbar и sticky-chrome (sidebar / lock-header) уезжает вверх. */}
      <div className="min-h-0 flex-1 overflow-y-auto px-[var(--space-2xl)] py-[var(--space-lg)]">
        <div className="flex max-w-[760px] flex-col gap-[var(--space-lg)]">
          {/* Number + Group — только при создании (бэк не разрешает менять
              key после создания, оставляем поля только в new-mode) */}
          <div className="grid grid-cols-[140px_1fr] gap-[var(--space-base)]">
            <div className="flex flex-col gap-[var(--space-xs)]">
              <Label className="text-[length:var(--text-sm)]">Номер</Label>
              <Input
                type="number"
                min={1}
                disabled={!canEdit || !isNew}
                {...form.register('number', { valueAsNumber: true })}
              />
              {isNew && !errors.number && (
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                  следующий свободный — можно изменить
                </span>
              )}
              {errors.number && (
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
                  {errors.number.message}
                </span>
              )}
            </div>
            <div className="flex flex-col gap-[var(--space-xs)]">
              <Label className="text-[length:var(--text-sm)]">Группа</Label>
              <Controller
                control={form.control}
                name="group"
                render={({ field }) => (
                  <Select
                    value={field.value}
                    onValueChange={field.onChange}
                    disabled={!canEdit}
                  >
                    <SelectTrigger size="sm" className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ALL_RULE_GROUPS.map((g) => (
                        <SelectItem key={g} value={g}>
                          {RULE_GROUP_LABELS[g]}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="flex flex-col gap-[var(--space-xs)]">
            <Label className="text-[length:var(--text-sm)]">Название</Label>
            <Input disabled={!canEdit} {...form.register('name')} />
            {errors.name && (
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
                {errors.name.message}
              </span>
            )}
          </div>

          <div className="flex flex-col gap-[var(--space-xs)]">
            <div className="flex items-baseline justify-between gap-[var(--space-base)]">
              <Label className="text-[length:var(--text-sm)]">
                Заметка для редактора
              </Label>
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                опционально · студент это не видит
              </span>
            </div>
            <textarea
              rows={2}
              disabled={!canEdit}
              placeholder="Например: подсказка для старших семестров с уже выбранной целью"
              {...form.register('description')}
              className="w-full resize-y rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
            />
          </div>

          {/* ── Условие ─────────────────────────────────────────────────
             Два режима: конструктор (builder) и сырой JSON. Source of truth —
             form.conditionJson. Builder синхронизирует tree → JSON на каждое
             изменение; JSON ↔ builder — через toggle с попыткой парсинга. */}
          <section className="flex flex-col gap-[var(--space-sm)]">
            <header className="flex items-baseline justify-between gap-[var(--space-base)]">
              <div className="flex items-baseline gap-[var(--space-xs)]">
                <h3 className="font-serif text-[length:var(--text-sm)] font-semibold tracking-tight text-[color:var(--color-text)]">
                  Условие
                </h3>
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                  когда это правило срабатывает
                </span>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={toggleConditionMode}
                disabled={!canEdit}
              >
                {conditionMode === 'simple' ? (
                  <>
                    <Code size={12} weight="regular" />
                    JSON-режим
                  </>
                ) : (
                  <>
                    <Sliders size={12} weight="regular" />
                    Конструктор
                  </>
                )}
              </Button>
            </header>

            {conditionMode === 'simple' ? (
              <ConditionBuilder
                value={tree}
                onChange={handleTreeChange}
                disabled={!canEdit}
              />
            ) : (
              <Controller
                control={form.control}
                name="conditionJson"
                render={({ field }) => (
                  <JsonField
                    label=""
                    hint="JSON: { all: [...] } / { any: [...] } / { param, op, value }"
                    rows={12}
                    disabled={!canEdit}
                    {...(errors.conditionJson?.message
                      ? { error: errors.conditionJson.message }
                      : {})}
                    value={field.value}
                    onChange={field.onChange}
                    onBlur={field.onBlur}
                    name={field.name}
                  />
                )}
              />
            )}

            {errors.conditionJson?.message && conditionMode === 'simple' && (
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
                {errors.conditionJson.message}
              </span>
            )}
          </section>

          <RecommendationBuilder form={form} disabled={!canEdit} />

          <div className="flex flex-col gap-[var(--space-xs)]">
            <div className="flex items-baseline justify-between gap-[var(--space-base)]">
              <Label className="text-[length:var(--text-sm)]">
                Приоритет правила
              </Label>
              <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                порядок в выводе Y1–Y6, если сработали несколько правил сразу
              </span>
            </div>
            <Controller
              control={form.control}
              name="priority"
              render={({ field }) => (
                <Select
                  value={String(field.value)}
                  onValueChange={(v) => field.onChange(Number(v))}
                  disabled={!canEdit}
                >
                  <SelectTrigger size="sm" className="w-[260px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {PRIORITY_LEVELS.map((l) => (
                      <SelectItem key={l.value} value={String(l.value)}>
                        <span className="flex items-baseline gap-[var(--space-sm)]">
                          <span>{l.label}</span>
                          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                            {l.hint}
                          </span>
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>
      </div>

      {/* ── Низ: действия ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-[var(--space-sm)] border-t border-[color:var(--color-border)] bg-[color:var(--color-bg)] px-[var(--space-2xl)] py-[var(--space-md)]">
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
          {dirty
            ? 'Несохранённые изменения · ⌘S — сохранить · ⌘↵ — сохранить + прогнать'
            : '⌘S — сохранить · ⌘↵ — сохранить и прогнать в sandbox'}
        </span>

        <div className="ml-auto flex items-center gap-[var(--space-sm)]">
          {!isNew && rule && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setConfirmDelete(true)}
                  disabled={!canEdit || isDeleting}
                >
                  <Trash size={14} />
                  Удалить
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {canEdit ? 'Удалить правило' : 'Сначала войди в редактор'}
              </TooltipContent>
            </Tooltip>
          )}

          {!isNew && rule && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => onPublishToggle(rule.id, isPublished)}
                  disabled={!canEdit || isPublishing || dirty}
                >
                  {isPublishing ? (
                    <CircleNotch size={14} className="animate-spin" />
                  ) : isPublished ? (
                    <EyeSlash size={14} />
                  ) : (
                    <Eye size={14} />
                  )}
                  {isPublished ? 'Снять с публикации' : 'Опубликовать'}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                {dirty
                  ? 'Сначала сохрани несохранённые изменения'
                  : isPublished
                    ? 'Студенты перестанут видеть рекомендации этого правила'
                    : 'Сделать видимым для студентов'}
              </TooltipContent>
            </Tooltip>
          )}

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                size="sm"
                onClick={() => submit()()}
                disabled={!canEdit || isSaving}
              >
                {isSaving ? (
                  <CircleNotch size={14} className="animate-spin" />
                ) : (
                  <FloppyDisk size={14} />
                )}
                {isNew || !rule ? 'Создать' : 'Сохранить'}
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {canEdit ? '⌘S' : 'Сначала войди в редактор'}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>

      {rule && (
        <ConfirmDialog
          open={confirmDelete}
          onOpenChange={setConfirmDelete}
          title={`Удалить R-${String(rule.number).padStart(3, '0')}?`}
          description={
            rule.is_published
              ? 'Правило опубликовано — студенты сразу перестанут получать его рекомендации.'
              : 'Правило в черновике — на студентов это не влияет.'
          }
          confirmLabel="Удалить"
          variant="danger"
          loading={isDeleting}
          onConfirm={() => {
            onDelete(rule.id)
            setConfirmDelete(false)
          }}
        />
      )}
    </form>
  )
}
