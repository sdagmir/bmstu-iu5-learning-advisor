import { useEffect, useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { FloppyDisk, Eye, Trash, CircleNotch, EyeSlash } from '@phosphor-icons/react'
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
import {
  NEW_RULE_DEFAULTS,
  parseJsonObject,
  ruleFormSchema,
  stringifyJson,
  type RuleFormValues,
} from './schema'
import { ALL_RULE_GROUPS, RULE_GROUP_LABELS } from '@/constants/enums'
import type { Rule, RuleCreate, RuleUpdate } from '@/types/api'

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
  onSaveCreate: (body: RuleCreate) => void
  onSaveUpdate: (id: string, body: RuleUpdate) => void
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
    recommendationJson: stringifyJson(rule.recommendation),
    priority: rule.priority,
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

  // Перезагружаем форму при смене правила или при выходе из новосоздания.
  useEffect(() => {
    if (isNew || !rule) {
      form.reset({ ...NEW_RULE_DEFAULTS, number: nextNumber })
    } else {
      form.reset(ruleToValues(rule))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rule?.id, isNew, nextNumber])

  const submit = (afterSave?: () => void) =>
    form.handleSubmit((values) => {
      try {
        const condition = parseJsonObject(values.conditionJson)
        const recommendation = parseJsonObject(values.recommendationJson)
        if (isNew || !rule) {
          onSaveCreate({
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
          onSaveUpdate(rule.id, {
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
      } catch (e) {
        form.setError('conditionJson', {
          message: 'JSON не парсится: ' + (e as Error).message,
        })
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
      className="flex h-full flex-col"
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

      {/* ── Скроллируемое тело ────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-[var(--space-2xl)] py-[var(--space-lg)]">
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
                <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
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
            <Label className="text-[length:var(--text-sm)]">Описание</Label>
            <textarea
              rows={2}
              disabled={!canEdit}
              {...form.register('description')}
              className="w-full resize-y rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
            />
          </div>

          <Controller
            control={form.control}
            name="conditionJson"
            render={({ field }) => (
              <JsonField
                label="Условие (condition)"
                hint="JSON: { all: [...] } / { any: [...] } / { param, op, value }"
                rows={14}
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

          <Controller
            control={form.control}
            name="recommendationJson"
            render={({ field }) => (
              <JsonField
                label="Шаблон рекомендации (recommendation)"
                hint="category, title, priority, reasoning + категорийные поля"
                rows={10}
                disabled={!canEdit}
                {...(errors.recommendationJson?.message
                  ? { error: errors.recommendationJson.message }
                  : {})}
                value={field.value}
                onChange={field.onChange}
                onBlur={field.onBlur}
                name={field.name}
              />
            )}
          />

          <div className="flex items-center gap-[var(--space-base)]">
            <Label className="text-[length:var(--text-sm)]">Приоритет</Label>
            <Input
              type="number"
              disabled={!canEdit}
              className="w-[100px]"
              {...form.register('priority', { valueAsNumber: true })}
            />
            <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
              чем больше, тем выше в списке Y1–Y6
            </span>
          </div>
        </div>
      </div>

      {/* ── Низ: действия ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-[var(--space-sm)] border-t border-[color:var(--color-border)] bg-[color:var(--color-bg)] px-[var(--space-2xl)] py-[var(--space-md)]">
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
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
