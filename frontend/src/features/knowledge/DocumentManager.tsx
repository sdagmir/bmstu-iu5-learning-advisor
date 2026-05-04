import { useState } from 'react'
import { CircleNotch, FilePlus, Trash } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useRagDelete, useRagUpload } from './useKnowledge'

/**
 * Управление документами RAG. Загрузка по `source` + длинному тексту,
 * удаление по `source`. Список загруженных документов на бэке отдельным
 * эндпоинтом не отдаётся (TODO бэка `GET /rag/documents`) — поэтому
 * показываем только формы.
 */
export function DocumentManager() {
  const upload = useRagUpload()
  const remove = useRagDelete()

  const [source, setSource] = useState('')
  const [text, setText] = useState('')
  const [deleteSource, setDeleteSource] = useState('')
  const [confirmOpen, setConfirmOpen] = useState(false)

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

  const submitDelete = (e: React.FormEvent) => {
    e.preventDefault()
    if (!deleteSource.trim()) return
    setConfirmOpen(true)
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
            Уникальная строка-идентификатор. Используется для удаления.
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

      {/* Delete */}
      <form
        onSubmit={submitDelete}
        className="flex flex-col gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-base)]"
      >
        <div className="flex flex-col gap-[var(--space-xs)]">
          <Label className="text-[length:var(--text-sm)]">
            Удалить по источнику
          </Label>
          <div className="flex gap-[var(--space-sm)]">
            <Input
              value={deleteSource}
              onChange={(e) => setDeleteSource(e.target.value)}
              placeholder="docs/syllabus/iu5-ml-introduction.md"
              disabled={remove.isPending}
            />
            <Button
              type="submit"
              variant="destructive"
              disabled={remove.isPending || !deleteSource.trim()}
            >
              {remove.isPending ? (
                <CircleNotch size={14} className="animate-spin" />
              ) : (
                <Trash size={14} />
              )}
              Удалить
            </Button>
          </div>
          <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Когда бэк отдаст GET /rag/documents — здесь появится полноценный
            список с inline-удалением.
          </span>
        </div>
      </form>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Удалить «${deleteSource}»?`}
        description="Все чанки этого источника пропадут из базы знаний."
        confirmLabel="Удалить"
        variant="danger"
        loading={remove.isPending}
        onConfirm={() => {
          remove.mutate(deleteSource.trim(), {
            onSuccess: () => {
              setDeleteSource('')
              setConfirmOpen(false)
            },
            onSettled: () => setConfirmOpen(false),
          })
        }}
      />
    </section>
  )
}
