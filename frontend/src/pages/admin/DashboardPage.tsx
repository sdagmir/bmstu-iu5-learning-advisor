import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import {
  Scales,
  UsersThree,
  BookOpen,
  Flask,
  ListMagnifyingGlass,
  ArrowRight,
} from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { Skeleton } from '@/components/ui/skeleton'
import { adminCatalogApi } from '@/features/catalog/adminApi'
import { rulesApi } from '@/features/rules/api'
import { useRagStats } from '@/features/knowledge/useKnowledge'
import { useAuthStore } from '@/stores/authStore'
import { routes } from '@/constants/routes'
import { cn } from '@/lib/utils'

/**
 * Phase 10 — admin-дашборд. Три счётчика (правила, юзеры, RAG-чанки) +
 * быстрые ссылки на ключевые admin-инструменты. Поднимает три параллельных
 * useQuery, рендерит Skeleton по отдельности (не блокируя другие цифры).
 */
export default function DashboardPage() {
  const email = useAuthStore((s) => s.user?.email ?? null)

  const rules = useQuery({
    queryKey: ['admin', 'rules'],
    queryFn: rulesApi.list,
    staleTime: 60_000,
  })
  const users = useQuery({
    queryKey: ['admin', 'catalog', 'users'],
    queryFn: adminCatalogApi.users.list,
    staleTime: 60_000,
  })
  const ragStats = useRagStats()

  const publishedRules = rules.data?.filter((r) => r.is_published).length ?? null
  const totalRules = rules.data?.length ?? null
  const totalUsers = users.data?.length ?? null
  const adminUsers = users.data?.filter((u) => u.role === 'admin').length ?? null

  return (
    <>
      <PageTopBar title="Дашборд" />
      <div className="flex flex-col gap-[var(--space-2xl)] px-[var(--space-2xl)] py-[var(--space-xl)]">
        <PageHeader
          title="Админ-панель"
          description={
            email
              ? `Привет, ${email}. Краткая сводка по системе.`
              : 'Краткая сводка по системе.'
          }
        />

        <div className="grid grid-cols-1 gap-[var(--space-base)] sm:grid-cols-3">
          <StatCard
            icon={<Scales size={18} weight="regular" />}
            label="Правил ЭС"
            value={totalRules}
            sub={
              publishedRules !== null && totalRules !== null
                ? `${publishedRules} опубликованных · ${totalRules - publishedRules} черновиков`
                : null
            }
            isLoading={rules.isLoading}
            isError={rules.isError}
            to={routes.admin.rules}
          />
          <StatCard
            icon={<UsersThree size={18} weight="regular" />}
            label="Пользователей"
            value={totalUsers}
            sub={
              adminUsers !== null && totalUsers !== null
                ? `${totalUsers - adminUsers} студентов · ${adminUsers} админов`
                : null
            }
            isLoading={users.isLoading}
            isError={users.isError}
            to={routes.admin.catalog('users')}
          />
          <StatCard
            icon={<BookOpen size={18} weight="regular" />}
            label="Чанков RAG"
            value={ragStats.data?.total_chunks ?? null}
            sub="Документов и фрагментов в базе знаний"
            isLoading={ragStats.isLoading}
            isError={ragStats.isError}
            to={routes.admin.knowledge}
          />
        </div>

        <section className="flex flex-col gap-[var(--space-md)]">
          <h3 className="text-[length:var(--text-sm)] font-semibold tracking-wider text-[color:var(--color-text-subtle)] uppercase">
            Быстрые ссылки
          </h3>
          <div className="grid grid-cols-1 gap-[var(--space-base)] sm:grid-cols-2">
            <QuickLink
              to={routes.admin.simulator}
              icon={<Flask size={18} weight="regular" />}
              title="Симулятор ЭС"
              description="Прогон любого профиля X1–X12 с трейсом 52 правил"
            />
            <QuickLink
              to={routes.admin.traces}
              icon={<ListMagnifyingGlass size={18} weight="regular" />}
              title="Debug-чат LLM"
              description="Один запрос — видим rules_fired, rag_chunks, tool_calls, profile_changes"
            />
          </div>
        </section>
      </div>
    </>
  )
}

interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: number | null
  sub: string | null
  isLoading: boolean
  isError: boolean
  to: string
}

function StatCard({ icon, label, value, sub, isLoading, isError, to }: StatCardProps) {
  return (
    <Link
      to={to}
      className={cn(
        'group flex flex-col gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-base)] transition-colors',
        'hover:border-[color:var(--color-border-strong)] hover:bg-[color:var(--color-surface-muted)]',
      )}
    >
      <div className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        {icon}
        {label}
      </div>
      {isLoading ? (
        <Skeleton className="h-9 w-24" />
      ) : isError ? (
        <span className="text-[length:var(--text-md)] text-[color:var(--color-danger)]">
          ошибка
        </span>
      ) : (
        <span className="font-serif text-[length:var(--text-2xl)] tabular-nums text-[color:var(--color-text)]">
          {value ?? '—'}
        </span>
      )}
      <div className="flex items-center justify-between gap-[var(--space-sm)]">
        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
          {sub ?? '—'}
        </span>
        <ArrowRight
          size={14}
          className="text-[color:var(--color-text-subtle)] transition-transform group-hover:translate-x-[2px] group-hover:text-[color:var(--color-primary)]"
        />
      </div>
    </Link>
  )
}

interface QuickLinkProps {
  to: string
  icon: React.ReactNode
  title: string
  description: string
}

function QuickLink({ to, icon, title, description }: QuickLinkProps) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-[var(--space-base)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-base)] transition-colors hover:border-[color:var(--color-border-strong)] hover:bg-[color:var(--color-surface-muted)]"
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[6px] bg-[color:var(--color-primary-soft)] text-[color:var(--color-primary)]">
        {icon}
      </div>
      <div className="flex min-w-0 flex-col gap-[2px]">
        <span className="text-[length:var(--text-base)] font-medium text-[color:var(--color-text)]">
          {title}
        </span>
        <span className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          {description}
        </span>
      </div>
      <ArrowRight
        size={14}
        className="ml-auto shrink-0 text-[color:var(--color-text-subtle)] transition-transform group-hover:translate-x-[2px] group-hover:text-[color:var(--color-primary)]"
      />
    </Link>
  )
}
