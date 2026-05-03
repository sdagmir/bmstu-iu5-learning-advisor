import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function HistoryPage() {
  return (
    <>
      <PageTopBar title="История" />
      <div className="mx-auto max-w-[1040px] px-[var(--space-2xl)] py-[var(--space-2xl)]">
        <PageHeader title="История" description="Фаза 6 — лента прошлых рекомендаций" />
        <EmptyState title="Stub" description="Фаза 6: архив рекомендаций с датами" />
      </div>
    </>
  )
}
