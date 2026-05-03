import { useParams } from 'react-router-dom'
import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function TraceDetailPage() {
  const { id } = useParams<{ id: string }>()
  return (
    <>
      <PageTopBar title="Трейс" />
      <div className="px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader title="Трейс запроса" description={`Фаза 10 — id: ${id}`} />
        <EmptyState
          title="Stub"
          description="4 секции: LLM prompt/response, function calls, RAG retrieval, rules fired"
        />
      </div>
    </>
  )
}
