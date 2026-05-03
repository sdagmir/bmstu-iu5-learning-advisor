import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function CoveragePage() {
  return (
    <>
      <PageTopBar title="Покрытие" />
      <div className="mx-auto max-w-[1040px] px-[var(--space-2xl)] py-[var(--space-2xl)]">
        <PageHeader title="Покрытие компетенций" description="Фаза 6 — радар имеешь / нужно" />
        <EmptyState title="Stub" description="Фаза 6: recharts radar + топ-5 пробелов" />
      </div>
    </>
  )
}
