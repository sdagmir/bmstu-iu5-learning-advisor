import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function KnowledgePage() {
  return (
    <>
      <PageTopBar title="База знаний" />
      <div className="px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader title="База знаний" description="Фаза 10 — документы RAG + тест-поиск" />
        <EmptyState title="Stub" />
      </div>
    </>
  )
}
