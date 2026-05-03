import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function TracesPage() {
  return (
    <>
      <PageTopBar title="Трейсы" />
      <div className="px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader title="Трейсы запросов" description="Фаза 10 — журнал запросов к ЭС/LLM/RAG" />
        <EmptyState title="Stub" />
      </div>
    </>
  )
}
