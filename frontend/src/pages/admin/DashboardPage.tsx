import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function DashboardPage() {
  return (
    <>
      <PageTopBar title="Дашборд" />
      <div className="px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader title="Дашборд" description="Фаза 7 — счётчики: правила, пользователи, документы" />
        <EmptyState title="Stub" />
      </div>
    </>
  )
}
