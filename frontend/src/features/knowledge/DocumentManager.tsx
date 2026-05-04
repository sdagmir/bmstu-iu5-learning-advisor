import { useState } from 'react'
import { CircleNotch, FilePlus, Trash } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useRagDelete, useRagDocuments, useRagUpload } from './useKnowledge'
import type { RagDocumentSummary } from '@/types/api'

/**
 * Управление документами RAG. Загрузка по `source` + длинному тексту,
 * inline-удаление из реального списка проиндексированных источников
 * (`GET /rag/documents`).
 */
export function DocumentManager() {
  const docs = useRagDocuments()
  const upload = useRagUpload()
  const remove = useRagDelete()

  const [source, setSource] = useState('')
  const [text, setText] = useState('')
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)

  const submitUpload = (e: React.FormEvent) => {
    e.preventDefault()
    if (!source.trim() || !text.trim()) return
    upload.mutate(
      { source: source.trim(), text: text.trim() },
      {
        onSuccess: () => {
          setSource('')
          setText('')
        },
      },
    )
  }

  return (
    <section className="flex flex-col gap-[var(--space-lg)]">
      <header className="flex flex-col gap-[var(--space-xs)]">
        <h2 className="text-[length:var(--text-md)] font-semibold text-[color:var(--color-text)]">
          Документы
        </h2>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Загрузка фрагментирует текст и индексирует в Qdrant. Удаление —
          по уникальному `source`.
        </p>
      </header>

      {/* Список проиндексированных источников */}
      <div className="flex flex-col gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)]">
        <div className="flex items-center justify-between gap-[var(--space-base)] border-b border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-sm)]">
          <span className="text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
            Проиндексировано {docs.data ? `· ${docs.data.length}` : ''}
          </span>
        </div>
        <DocumentList
          docs={docs.data}
          isLoading={docs.isLoading}
          isError={docs.isError}
          onAskDelete={setPendingDelete}
          deletingSource={remove.isPending ? pendingDelete : null}
        />
      </div>

      {/* Upload */}
      <form
        onSubmit={submitUpload}
        className="flex flex-col gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-base)]"
      >
        <div className="flex flex-col gap-[var(--space-xs)]">
          <Label className="text-[length:var(--text-sm)]">Источник (`source`)</Label>
          <Input
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="docs/syllabus/iu5-ml-introduction.md"
            disabled={upload.isPending}
          />
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Уникальная строка-идентификатор. При повторной загрузке с тем же
            `source` старые чанки заменяются.
          </span>
        </div>
        <div className="flex flex-col gap-[var(--space-xs)]">
          <Label className="text-[length:var(--text-sm)]">Текст документа</Label>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={upload.isPending}
            rows={6}
            placeholder="Полный текст. Будет автоматически нарезан на чанки."
            className="w-full resize-y rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
          />
        </div>
        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={upload.isPending || !source.trim() || !text.trim()}
          >
            {upload.isPending ? (
              <CircleNotch size={14} className="animate-spin" />
            ) : (
              <FilePlus size={14} weight="regular" />
            )}
            Загрузить
          </Button>
        </div>
      </form>

      <ConfirmDialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
        title={pendingDelete ? `Удалить «${pendingDelete}»?` : ''}
        description="Все чанки этого источника пропадут из базы знаний."
        confirmLabel="Удалить"
        variant="danger"
        loading={remove.isPending}
        onConfirm={() => {
          if (!pendingDelete) return
          remove.mutate(pendingDelete, {
            onSettled: () => setPendingDelete(null),
          })
        }}
      />
    </section>
  )
}

interface DocumentListProps {
  docs: RagDocumentSummary[] | undefined
  isLoading: boolean
  isError: boolean
  onAskDelete: (source: string) => void
  deletingSource: string | null
}

function DocumentList({
  docs,
  isLoading,
  isError,
  onAskDelete,
  deletingSource,
}: DocumentListProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-[var(--space-xs)] p-[var(--space-base)]">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-9 w-full" />
        ))}
      </div>
    )
  }
  if (isError) {
    return (
      <p className="px-[var(--space-base)] py-[var(--space-md)] text-[length:var(--text-sm)] text-[color:var(--color-danger)]">
        Не удалось загрузить список документов.
      </p>
    )
  }
  if (!docs || docs.length === 0) {
    return (
      <p className="px-[var(--space-base)] py-[var(--space-md)] text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
        Пусто. Загрузи первый документ ниже.
      </p>
    )
  }

  return (
    <ul className="flex flex-col">
      {docs.map((d) => (
        <li
          key={d.source}
          className="flex items-center justify-between gap-[var(--space-base)] border-b border-[color:var(--color-border)] px-[var(--space-base)] py-[var(--space-sm)] last:border-b-0"
        >
          <div className="flex min-w-0 flex-col gap-[2px]">
            <span className="truncate font-mono text-[length:var(--text-sm)] text-[color:var(--color-text)]">
              {d.source}
            </span>
            <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)] tabular-nums">
              {d.chunks_count}{' '}
              {chunkLabel(d.chunks_count)}
              {d.indexed_at && ` · ${formatDate(d.indexed_at)}`}
            </span>
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onAskDelete(d.source)}
                disabled={deletingSource === d.source}
                aria-label={`Удалить документ ${d.source}`}
              >
                {deletingSource === d.source ? (
                  <CircleNotch size={14} className="animate-spin" />
                ) : (
                  <Trash size={14} className="text-[color:var(--color-danger)]" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent>Удалить документ</TooltipContent>
          </Tooltip>
        </li>
      ))}
    </ul>
  )
}

function chunkLabel(n: number): string {
  const mod10 = n % 10
  const mod100 = n % 100
  if (mod10 === 1 && mod100 !== 11) return 'чанк'
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'чанка'
  return 'чанков'
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
