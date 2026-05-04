import { useRef, useState } from 'react'
import { toast } from 'sonner'
import { CircleNotch, FilePlus, FolderOpen, Trash } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useRagDelete, useRagDocuments, useRagUpload } from './useKnowledge'
import type { RagDocumentSummary } from '@/types/api'

// Бэк не парсит бинарные форматы — только plain text. Большой текст всё равно
// нарежется на чанки, но крупный файл дольше эмбеддится через OpenRouter.
const SOFT_LIMIT_CHARS = 50_000

/**
 * Управление документами RAG. Загрузка по `name` (идентификатор для
 * upsert/delete) + plain-text содержимому, либо через выбор .txt/.md файла.
 * Inline-удаление из реального списка проиндексированных источников.
 */
export function DocumentManager() {
  const docs = useRagDocuments()
  const upload = useRagUpload()
  const remove = useRagDelete()

  const [name, setName] = useState('')
  const [text, setText] = useState('')
  const [pendingDelete, setPendingDelete] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const submitUpload = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim() || !text.trim()) return
    upload.mutate(
      { source: name.trim(), text: text.trim() },
      {
        onSuccess: () => {
          setName('')
          setText('')
        },
      },
    )
  }

  const onPickFile = () => fileInputRef.current?.click()

  const onFileSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    e.target.value = '' // позволить выбрать тот же файл повторно
    if (!file) return

    // .txt/.md — единственное что бэк примет без парсера. PDF/docx и пр.
    // придут как бинарные байты и индексирующий API сломается.
    const ok = /\.(txt|md|markdown)$/i.test(file.name) || file.type.startsWith('text/')
    if (!ok) {
      toast.error('Поддерживаются только .txt и .md — PDF/docx надо сконвертировать в текст вручную')
      return
    }

    try {
      const content = await file.text()
      setText(content)
      // Если name пустой — подставляем имя файла без расширения
      if (!name.trim()) {
        const base = file.name.replace(/\.(txt|md|markdown)$/i, '')
        setName(base)
      }
    } catch {
      toast.error('Не удалось прочитать файл')
    }
  }

  const charCount = text.length
  const tooBig = charCount > SOFT_LIMIT_CHARS

  return (
    <section className="flex flex-col gap-[var(--space-lg)]">
      <header className="flex flex-col gap-[var(--space-xs)]">
        <h2 className="text-[length:var(--text-md)] font-semibold text-[color:var(--color-text)]">
          Документы
        </h2>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Загрузи .txt/.md или вставь текст — он порежется на чанки и
          проиндексируется в Qdrant. Удаление по названию.
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
          <Label className="text-[length:var(--text-sm)]">Название</Label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="ml-introduction"
            disabled={upload.isPending}
          />
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Уникальный идентификатор — латиницей или кириллицей, без пробелов.
            Используется чтобы потом найти и удалить документ. Повторная
            загрузка с тем же названием перезаписывает старые чанки.
          </span>
        </div>

        <div className="flex flex-col gap-[var(--space-xs)]">
          <div className="flex items-baseline justify-between gap-[var(--space-sm)]">
            <Label className="text-[length:var(--text-sm)]">Содержимое</Label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.md,.markdown,text/plain,text/markdown"
              onChange={onFileSelected}
              className="hidden"
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={onPickFile}
              disabled={upload.isPending}
            >
              <FolderOpen size={14} weight="regular" />
              Выбрать файл .txt/.md
            </Button>
          </div>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={upload.isPending}
            placeholder="Вставь текст или выбери файл выше. Бинарные форматы (PDF, docx) не поддерживаются — конвертируй в текст вручную."
            className="min-h-[140px] w-full rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-md)] py-[var(--space-sm)] text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)] outline-none focus-visible:border-[color:var(--color-primary)] focus-visible:ring-[3px] focus-visible:ring-[color:var(--color-primary-soft)] disabled:cursor-not-allowed disabled:opacity-60"
          />
          <div className="flex items-baseline justify-between gap-[var(--space-sm)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            <span>
              Большие документы лучше резать вручную на куски ~20–30K символов —
              эмбеддинги через OpenRouter дольше обрабатывают крупный текст.
            </span>
            <span
              className={`tabular-nums ${tooBig ? 'text-[color:var(--color-danger)]' : ''}`}
            >
              {charCount.toLocaleString('ru-RU')} / {SOFT_LIMIT_CHARS.toLocaleString('ru-RU')}
            </span>
          </div>
        </div>

        <div className="flex justify-end">
          <Button
            type="submit"
            disabled={upload.isPending || !name.trim() || !text.trim()}
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
