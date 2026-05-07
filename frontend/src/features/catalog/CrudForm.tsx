import { useEffect, useMemo, useState } from 'react'
import {
  useForm,
  Controller,
  type Path,
  type DefaultValues,
  type Resolver,
  type Control,
} from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { CircleNotch } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import type { EntityConfig, FieldConfig, SelectOption } from './EntityConfig'

interface CrudFormProps<TRead extends { id: string }, TForm> {
  config: EntityConfig<TRead, TForm>
  open: boolean
  onOpenChange: (open: boolean) => void
  /** `null` — режим создания, иначе — редактирование. */
  row: TRead | null
  isSaving: boolean
  onSubmit: (values: TForm) => void
}

/**
 * Универсальная форма CRUD. По `EntityConfig.fields` рендерит контролы
 * (text / textarea / number / select / multiselect / switch). Submit
 * валидирует через `config.schema` и зовёт `onSubmit`.
 *
 * MVP-выбор: multiselect — это compact чип-список с toggle-режимом.
 * Полноценный combobox с поиском не делаем — для 30 компетенций это overkill.
 */
export function CrudForm<TRead extends { id: string }, TForm extends Record<string, unknown>>({
  config,
  open,
  onOpenChange,
  row,
  isSaving,
  onSubmit,
}: CrudFormProps<TRead, TForm>) {
  const isEdit = row !== null
  const mode: 'create' | 'edit' = isEdit ? 'edit' : 'create'

  const visibleFields = useMemo(
    () => config.fields.filter((f) => !f.showIn || f.showIn.includes(mode)),
    [config.fields, mode],
  )

  const defaultValues = useMemo<DefaultValues<TForm>>(
    () =>
      (isEdit && row ? config.toFormValues(row) : config.emptyFormValues()) as DefaultValues<TForm>,
    [isEdit, row, config],
  )

  const resolver = zodResolver(
    config.schema as never,
  ) as unknown as Resolver<TForm>
  const form = useForm<TForm>({
    resolver,
    defaultValues,
  })

  // На каждое открытие диалога — сбрасываем форму к актуальным данным.
  useEffect(() => {
    if (open) form.reset(defaultValues)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, row?.id])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[85vh] max-w-[560px] flex-col gap-0 p-0">
        <DialogHeader className="px-[var(--space-2xl)] pt-[var(--space-xl)] pb-[var(--space-base)]">
          <DialogTitle>
            {isEdit ? `Редактировать ${config.singular}` : `Создать ${config.singular}`}
          </DialogTitle>
          {isEdit && row && (
            <DialogDescription className="text-[color:var(--color-text-muted)]">
              {config.rowLabel(row)}
            </DialogDescription>
          )}
        </DialogHeader>

        <form
          onSubmit={form.handleSubmit((values) => onSubmit(values as TForm))}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="flex-1 overflow-y-auto px-[var(--space-2xl)] py-[var(--space-base)]">
            <div className="flex flex-col gap-[var(--space-base)]">
              {visibleFields.map((field) => (
                <FieldRow
                  key={field.name}
                  field={field}
                  control={form.control as unknown as Control<TForm>}
                  register={form.register}
                  error={form.formState.errors[field.name]?.message as string | undefined}
                  readOnly={isEdit && Boolean(field.readOnlyOnEdit)}
                />
              ))}
            </div>
          </div>

          <DialogFooter className="border-t border-[color:var(--color-border)] px-[var(--space-2xl)] py-[var(--space-base)]">
            <Button
              type="button"
              variant="ghost"
              onClick={() => onOpenChange(false)}
              disabled={isSaving}
            >
              Отмена
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving && <CircleNotch size={14} className="animate-spin" />}
              {isEdit ? 'Сохранить' : 'Создать'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

interface FieldRowProps<TForm extends Record<string, unknown>> {
  field: FieldConfig<TForm>
  // Чтобы не возиться со сложными generic'ами для control/register —
  // проксируем как unknown-проп. Все типы зафиксированы выше через `useForm<TForm>`.
  control: ReturnType<typeof useForm<TForm>>['control']
  register: ReturnType<typeof useForm<TForm>>['register']
  error?: string | undefined
  readOnly?: boolean | undefined
}

function FieldRow<TForm extends Record<string, unknown>>({
  field,
  control,
  register,
  error,
  readOnly,
}: FieldRowProps<TForm>) {
  const name = field.name as Path<TForm>

  // Switch — inline-строка: лейбл слева растягивается, control справа фикс-ширины.
  // Иначе одинокий 32px-свитч под полноширинным лейблом смотрится сиротой.
  if (field.type === 'switch') {
    return (
      <div className="flex flex-col gap-[var(--space-xs)]">
        <div className="flex items-center justify-between gap-[var(--space-base)]">
          <Label className="text-[length:var(--text-sm)]">{field.label}</Label>
          <Controller
            control={control}
            name={name}
            render={({ field: f }) => (
              <Switch
                checked={Boolean(f.value)}
                onCheckedChange={f.onChange}
                disabled={readOnly}
                className="shrink-0"
              />
            )}
          />
        </div>
        {field.hint && (
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            {field.hint}
          </span>
        )}
        {error && (
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
            {error}
          </span>
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-[var(--space-xs)]">
      <Label className="text-[length:var(--text-sm)]">{field.label}</Label>
      {renderControl()}
      {field.hint && (
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
          {field.hint}
        </span>
      )}
      {error && (
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-danger)]">
          {error}
        </span>
      )}
    </div>
  )

  function renderControl() {
    if (field.type === 'text') {
      return (
        <Input
          {...register(name)}
          placeholder={field.placeholder}
          readOnly={readOnly}
          disabled={readOnly}
        />
      )
    }
    if (field.type === 'number') {
      return (
        <Input
          type="number"
          {...register(name, { valueAsNumber: true })}
          placeholder={field.placeholder}
          readOnly={readOnly}
          disabled={readOnly}
        />
      )
    }
    if (field.type === 'textarea') {
      return (
        <textarea
          rows={3}
          readOnly={readOnly}
          disabled={readOnly}
          placeholder={field.placeholder}
          {...register(name)}
          className="w-full resize-y rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
        />
      )
    }
    if (field.type === 'select') {
      return (
        <Controller
          control={control}
          name={name}
          render={({ field: f }) => (
            <StaticSelect
              value={f.value as string | undefined}
              onValueChange={f.onChange}
              options={field.options}
              placeholder={field.placeholder}
              disabled={readOnly}
            />
          )}
        />
      )
    }
    if (field.type === 'multiselect') {
      return (
        <Controller
          control={control}
          name={name}
          render={({ field: f }) => (
            <ChipMultiSelect
              value={(f.value as string[] | undefined) ?? []}
              onChange={f.onChange}
              options={field.options}
              disabled={readOnly}
            />
          )}
        />
      )
    }
    return null
  }
}

interface StaticSelectProps {
  value: string | undefined
  onValueChange: (v: string) => void
  options: FieldConfig<Record<string, unknown>>['options']
  placeholder?: string | undefined
  disabled?: boolean | undefined
}

/**
 * Статичные опции — берутся синхронно. Если `options` — функция, отправляем
 * её в lazy-resolve через useResolveOptions, чтобы динамические select'ы
 * (например, список карьерных направлений) тоже работали.
 */
function StaticSelect({ value, onValueChange, options, placeholder, disabled }: StaticSelectProps) {
  const resolved = useResolveOptions(options)
  return (
    <Select
      onValueChange={onValueChange}
      {...(disabled !== undefined ? { disabled } : {})}
      {...(value !== undefined && value !== '' ? { value } : {})}
    >
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder ?? 'Выбрать…'} />
      </SelectTrigger>
      <SelectContent>
        {resolved.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface ChipMultiSelectProps {
  value: string[]
  onChange: (next: string[]) => void
  options: FieldConfig<Record<string, unknown>>['options']
  disabled?: boolean | undefined
}

/**
 * Чипо-мультиселект. Все опции рендерим как кликабельные «чипы» —
 * выбранные в заливке primary-soft, не выбранные — в обводке.
 * Для 30+ компетенций тоже читается; если станет больше — добавим поиск.
 */
function ChipMultiSelect({ value, onChange, options, disabled }: ChipMultiSelectProps) {
  const resolved = useResolveOptions(options)
  const set = new Set(value)

  const toggle = (id: string) => {
    if (disabled) return
    const next = new Set(set)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    onChange(Array.from(next))
  }

  if (resolved.length === 0) {
    return (
      <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
        Список пуст
      </span>
    )
  }

  // Грид с равными колонками: ширина каждого чипа автоматически одинаковая
  // (по самой широкой ячейке через `minmax(0,1fr)`), длинные лейблы переносятся
  // на 2 строки (`line-clamp-2`). Высота строки фикс через `auto-rows`, чтобы
  // одно- и двухстрочные чипы смотрелись одинаковой высоты.
  return (
    <div className="grid auto-rows-11 grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-[var(--space-xs)]">
      {resolved.map((o) => {
        const isOn = set.has(o.value)
        return (
          <button
            key={o.value}
            type="button"
            onClick={() => toggle(o.value)}
            disabled={disabled}
            aria-pressed={isOn}
            title={o.label}
            className={cn(
              'flex h-full min-w-0 items-center justify-center rounded-[999px] border px-[var(--space-md)] text-center text-[length:var(--text-sm)] leading-tight transition-colors disabled:cursor-not-allowed disabled:opacity-60',
              isOn
                ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary-soft)] font-medium text-[color:var(--color-primary)]'
                : 'border-[color:var(--color-border)] text-[color:var(--color-text-muted)] hover:border-[color:var(--color-border-strong)] hover:text-[color:var(--color-text)]',
            )}
          >
            <span className="line-clamp-2">{o.label}</span>
          </button>
        )
      })}
    </div>
  )
}

/**
 * Резолвит `options` (массив или async-функцию) в массив. Статичные —
 * через `useMemo` (никаких setState), async — через стейт + эффект.
 */
function useResolveOptions(
  options: FieldConfig<Record<string, unknown>>['options'],
): SelectOption[] {
  const staticValue = useMemo<SelectOption[]>(
    () => (Array.isArray(options) ? options : []),
    [options],
  )
  const isAsync = typeof options === 'function'
  const [asyncValue, setAsyncValue] = useState<SelectOption[]>([])

  useEffect(() => {
    if (!isAsync || typeof options !== 'function') return
    let cancelled = false
    Promise.resolve(options()).then((res) => {
      if (!cancelled) setAsyncValue(res)
    })
    return () => {
      cancelled = true
    }
  }, [isAsync, options])

  return isAsync ? asyncValue : staticValue
}
