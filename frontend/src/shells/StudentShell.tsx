import { NavLink, Outlet } from 'react-router-dom'
import {
  House,
  ChatCircle,
  ChartPolar,
  User,
  ClockCounterClockwise,
  Gear,
  SignOut,
} from '@phosphor-icons/react'
import { useAuthStore } from '@/stores/authStore'
import { useAuth } from '@/features/auth/useAuth'
import { routes } from '@/constants/routes'
import { Logo } from '@/components/common/Logo'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: routes.home, label: 'Главная', icon: House, end: true },
  { to: routes.chat, label: 'Чат', icon: ChatCircle, end: false },
  { to: routes.coverage, label: 'Покрытие', icon: ChartPolar, end: false },
  { to: routes.profile, label: 'Профиль', icon: User, end: false },
  { to: routes.history, label: 'История', icon: ClockCounterClockwise, end: false },
]

/**
 * Студенческая оболочка: левый rail (навигация + блок юзера) + контент.
 * На мобильных rail ещё не схлопнут — это фаза 5 (чат требует mobile).
 */
export function StudentShell() {
  // Узкие селекторы — шелл не ре-рендерится при правке полей профиля.
  const email = useAuthStore((s) => s.user?.email ?? null)
  const role = useAuthStore((s) => s.user?.role ?? null)
  const { logout } = useAuth()
  // Имя для отображения: пока полного имени нет в API, показываем
  // префикс email до '@'. Когда бэк добавит full_name — заменим тут.
  const displayName = email ? email.split('@')[0] : '—'

  return (
    <div className="flex h-svh">
      <aside className="flex w-[240px] shrink-0 flex-col overflow-y-auto border-r border-[color:var(--color-border)] px-[var(--space-lg)] py-[var(--space-xl)]">
        <Logo className="mb-[var(--space-2xl)] px-[var(--space-sm)]" />

        <nav className="flex flex-1 flex-col gap-[2px]">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-[var(--space-sm)] rounded-[6px] px-[var(--space-sm)] py-[var(--space-sm)] text-[length:var(--text-base)] transition-colors',
                  isActive
                    ? 'bg-[color:var(--color-primary-soft)] font-semibold text-[color:var(--color-primary)]'
                    : 'text-[color:var(--color-text-muted)] hover:bg-[color:var(--color-surface-muted)] hover:text-[color:var(--color-text)]',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={20} weight={isActive ? 'bold' : 'regular'} />
                  {label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="mt-[var(--space-base)] flex flex-col gap-[var(--space-sm)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
          {role === 'admin' && (
            <NavLink
              to={routes.admin.root}
              className="flex items-center gap-[var(--space-sm)] rounded-[6px] px-[var(--space-sm)] py-[var(--space-sm)] text-[length:var(--text-base)] text-[color:var(--color-text-muted)] transition-colors hover:bg-[color:var(--color-surface-muted)] hover:text-[color:var(--color-text)]"
            >
              <Gear size={20} weight="regular" />
              Админ-режим
            </NavLink>
          )}

          <div className="flex items-center justify-between gap-[var(--space-sm)] px-[var(--space-sm)]">
            <div className="min-w-0">
              <div className="truncate text-[length:var(--text-sm)] font-medium text-[color:var(--color-text)]">
                {displayName}
              </div>
              <div className="truncate text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                {email}
              </div>
            </div>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  type="button"
                  aria-label="Выйти"
                  onClick={() => logout.mutate()}
                  disabled={logout.isPending}
                  className="shrink-0 rounded-[6px] p-[var(--space-sm)] text-[color:var(--color-text-muted)] transition-colors hover:bg-[color:var(--color-surface-muted)] hover:text-[color:var(--color-text)] disabled:opacity-50"
                >
                  <SignOut size={18} weight="regular" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="top">Выйти</TooltipContent>
            </Tooltip>
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-x-hidden overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
