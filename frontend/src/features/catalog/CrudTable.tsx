import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { MagnifyingGlass, PencilSimple, Plus, Trash } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { CrudForm } from './CrudForm'
import type { EntityConfig } from './EntityConfig'
import { cn } from '@/lib/utils'

interface CrudTableProps<TRead extends { id: string }, TForm> {
  config: EntityConfig<TRead, TForm>
}

/**
 * Generic-таблица CRUD. Список + поиск + кнопки create/edit/delete + диалог
 * формы. Все мутации проходят invalidate'ом по ключу `['admin', 'catalog', key]`.
 *
 * Удаление — через `ConfirmDialog`. Кнопка create скрывается если
 * у конфига нет `create` (например, users).
 */
export function CrudTable<TRead extends { id: string }, TForm extends Record<string, unknown>>({
  config,
}: CrudTableProps<TRead, TForm>) {
  const queryClient = useQueryClient()
  const queryKey = useMemo(() => ['admin', 'catalog', config.key] as const, [config.key])

  const list = useQuery({ queryKey, queryFn: config.list })

  const invalidate = () => queryClient.invalidateQueries({ queryKey })

  const create = useMutation({
    mutationFn: (body: TForm) => config.create!(body),
    onSuccess: () => {
      toast.success(`Создано: ${config.singular}`)
      void invalidate()
    },
    onError: (err: Error) => toast.error(err.message || 'Не удалось создать'),
  })

  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: Partial<TForm> }) => config.update!(id, body),
    onSuccess: () => {
      toast.success('Сохранено')
      void invalidate()
    },
    onError: (err: Error) => toast.error(err.message || 'Не удалось сохранить'),
  })

  const remove = useMutation({
    mutationFn: (id: string) => config.delete!(id),
    onSuccess: () => {
      toast.success('Удалено')
      void invalidate()
    },
    onError: (err: Error) => toast.error(err.message || 'Не удалось удалить'),
  })

  const [query, setQuery] = useState('')
  const [editingRow, setEditingRow] = useState<TRead | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [confirmRow, setConfirmRow] = useState<TRead | null>(null)

  const visibleRows = useMemo(() => {
    if (!list.data) return []
    const q = query.trim().toLowerCase()
    if (!q) return list.data
    return list.data.filter((row) => config.rowLabel(row).toLowerCase().includes(q))
  }, [list.data, query, config])

  const startCreate = () => {
    setEditingRow(null)
    setFormOpen(true)
  }
  const startEdit = (row: TRead) => {
    setEditingRow(row)
    setFormOpen(true)
  }

  const onSubmit = (values: TForm) => {
    if (editingRow) {
      update.mutate(
        { id: editingRow.id, body: values },
        { onSuccess: () => setFormOpen(false) },
      )
    } else {
      create.mutate(values, { onSuccess: () => setFormOpen(false) })
    }
  }

  const totalCols = config.columns.length + (config.update || config.delete ? 1 : 0)

  return (
    <div className="flex flex-col gap-[var(--space-base)] px-[var(--space-2xl)] py-[var(--space-lg)]">
      <div className="flex flex-wrap items-center gap-[var(--space-base)]">
        <div className="relative min-w-[200px] flex-1 sm:max-w-[360px]">
          <MagnifyingGlass
            size={14}
            className="pointer-events-none absolute top-1/2 left-[var(--space-sm)] -translate-y-1/2 text-[color:var(--color-text-subtle)]"
          />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Поиск: ${config.pluralName.toLowerCase()}…`}
            className="pl-[calc(var(--space-sm)+1.25rem)]"
          />
        </div>
        <span className="text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
          {list.data ? `${visibleRows.length} из ${list.data.length}` : '…'}
        </span>
        <div className="ml-auto">
          {config.create && (
            <Button onClick={startCreate}>
              <Plus size={14} weight="bold" />
              Создать
            </Button>
          )}
        </div>
      </div>

      <div className="overflow-hidden rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)]">
        {/* Header — gap должен совпадать с body, иначе колонки разъезжаются */}
        <div
          className="grid gap-[var(--space-base)] border-b border-[color:var(--color-border)] bg-[color:var(--color-surface-muted)] px-[var(--space-base)] py-[var(--space-sm)] text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase"
          style={{ gridTemplateColumns: buildGridCols(config.columns, totalCols) }}
        >
          {config.columns.map((col) => (
            <span key={col.key}>{col.label}</span>
          ))}
          {(config.update || config.delete) && <span />}
        </div>

        {/* Body */}
        {list.isLoading ? (
          <RowSkeleton rows={6} cols={totalCols} />
        ) : visibleRows.length === 0 ? (
          <div className="px-[var(--space-base)] py-[var(--space-3xl)] text-center text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
            {list.data && list.data.length === 0
              ? `Пока ничего нет. ${config.create ? 'Создай первую запись.' : ''}`
              : 'Ничего не нашлось'}
          </div>
        ) : (
          <div className="divide-y divide-[color:var(--color-border)]">
            {visibleRows.map((row) => (
              <div
                key={row.id}
                className={cn(
                  'grid items-center gap-[var(--space-base)] px-[var(--space-base)] py-[var(--space-sm)] text-[length:var(--text-sm)] transition-colors hover:bg-[color:var(--color-surface-muted)]',
                )}
                style={{ gridTemplateColumns: buildGridCols(config.columns, totalCols) }}
              >
                {config.columns.map((col) => (
                  <div
                    key={col.key}
                    className={cn(
                      'min-w-0 truncate',
                      col.mono && 'font-mono tabular-nums text-[color:var(--color-text-muted)]',
                    )}
                  >
                    {col.render ? col.render(row) : formatValue(row[col.key])}
                  </div>
                ))}
                {(config.update || config.delete) && (
                  <div className="flex justify-end gap-[var(--space-xs)]">
                    {config.update && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => startEdit(row)}
                            aria-label="Редактировать"
                          >
                            <PencilSimple size={14} />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Редактировать</TooltipContent>
                      </Tooltip>
                    )}
                    {config.delete && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={() => setConfirmRow(row)}
                            aria-label="Удалить"
                          >
                            <Trash size={14} />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Удалить</TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <CrudForm
        config={config}
        open={formOpen}
        onOpenChange={setFormOpen}
        row={editingRow}
        isSaving={create.isPending || update.isPending}
        onSubmit={onSubmit}
      />

      <ConfirmDialog
        open={confirmRow !== null}
        onOpenChange={(open) => !open && setConfirmRow(null)}
        title={`Удалить «${confirmRow ? config.rowLabel(confirmRow) : ''}»?`}
        description="Действие нельзя отменить."
        confirmLabel="Удалить"
        variant="danger"
        loading={remove.isPending}
        onConfirm={() => {
          if (!confirmRow) return
          remove.mutate(confirmRow.id, { onSuccess: () => setConfirmRow(null) })
        }}
      />
    </div>
  )
}

function buildGridCols<TRead>(
  columns: Array<{ key: keyof TRead & string; width?: number }>,
  total: number,
): string {
  const tracks = columns.map((c) => (c.width ? `${c.width}px` : 'minmax(0, 1fr)'))
  if (total > columns.length) tracks.push('120px') // actions column
  return tracks.join(' ')
}

function formatValue(v: unknown): string {
  if (v === null || v === undefined) return '—'
  if (typeof v === 'boolean') return v ? 'Да' : 'Нет'
  if (typeof v === 'number') return String(v)
  if (typeof v === 'string') return v
  if (Array.isArray(v)) return `${v.length} шт`
  return ''
}

function RowSkeleton({ rows, cols }: { rows: number; cols: number }) {
  return (
    <div className="divide-y divide-[color:var(--color-border)]">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="grid items-center gap-[var(--space-base)] px-[var(--space-base)] py-[var(--space-md)]"
          style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
        >
          {Array.from({ length: cols }).map((_, j) => (
            <Skeleton key={j} className="h-4" style={{ width: `${50 + ((i + j) * 7) % 40}%` }} />
          ))}
        </div>
      ))}
    </div>
  )
}
