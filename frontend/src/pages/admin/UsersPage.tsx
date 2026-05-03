import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { EmptyState } from '@/components/common/EmptyState'

export default function UsersPage() {
  return (
    <>
      <PageTopBar title="Пользователи" />
      <div className="px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader title="Пользователи" description="Фаза 10 — список студентов и ролей" />
        <EmptyState title="Stub" />
      </div>
    </>
  )
}
