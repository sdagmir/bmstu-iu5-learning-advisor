import { BookOpen } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { TestSearchPanel } from '@/features/knowledge/TestSearchPanel'
import { DocumentManager } from '@/features/knowledge/DocumentManager'
import { useRagStats } from '@/features/knowledge/useKnowledge'

/**
 * Phase 10 — База знаний RAG. Две колонки: тест-поиск (для отладки выдачи)
 * и менеджер документов (загрузка / удаление по source). Список документов
 * показать пока не можем — нет эндпоинта (TODO бэка).
 */
export default function KnowledgePage() {
  const stats = useRagStats()
  const total = stats.data?.total_chunks

  return (
    <>
      <PageTopBar
        title="База знаний"
        icon={<BookOpen size={18} weight="regular" />}
        actions={
          total !== undefined ? (
            <span className="text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
              {total} чанков
            </span>
          ) : null
        }
      />

      <div className="grid grid-cols-1 gap-[var(--space-2xl)] px-[var(--space-2xl)] py-[var(--space-xl)] lg:grid-cols-[1fr_1fr]">
        <TestSearchPanel />
        <DocumentManager />
      </div>
    </>
  )
}
