import { NavLink, Outlet } from 'react-router-dom'
import {
  SquaresFour,
  Scales,
  Flask,
  Stack,
  BookOpen,
  UsersThree,
  ListMagnifyingGlass,
  ArrowUUpLeft,
} from '@phosphor-icons/react'
import { routes } from '@/constants/routes'
import { Logo } from '@/components/common/Logo'
import { cn } from '@/lib/utils'

const NAV_ITEMS = [
  { to: routes.admin.root, label: 'Дашборд', icon: SquaresFour, end: true },
  { to: routes.admin.rules, label: 'Правила', icon: Scales, end: false },
  { to: routes.admin.simulator, label: 'Симулятор', icon: Flask, end: false },
  { to: routes.admin.traces, label: 'Трейсы', icon: ListMagnifyingGlass, end: false },
  { to: routes.admin.catalog('competencies'), label: 'Каталог', icon: Stack, end: false },
  { to: routes.admin.knowledge, label: 'База знаний', icon: BookOpen, end: false },
  { to: routes.admin.users, label: 'Пользователи', icon: UsersThree, end: false },
]

/**
 * Админская оболочка: левый sidebar (плотный) + контент без max-width.
 * Desktop-only. На узких экранах — заглушка (фаза 7 добавит её).
 *
 * Header-lockup: серифный лого + моно-тег `admin/` — engineering-console
 * акцент, без капсового «АДМИНИСТРАТИВНЫЙ РЕЖИМ».
 */
export function AdminShell() {
  return (
    <div className="flex h-svh">
      <aside className="flex w-[240px] shrink-0 flex-col overflow-y-auto border-r border-[color:var(--color-border)] bg-[color:var(--color-surface-muted)] px-[var(--space-md)] py-[var(--space-xl)]">
        <div className="mb-[var(--space-xl)] flex flex-col gap-[var(--space-xs)] px-[var(--space-sm)]">
          <Logo />
          <div className="font-mono text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            admin/
          </div>
        </div>

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
                    : 'text-[color:var(--color-text-muted)] hover:bg-[color:var(--color-surface-hover)] hover:text-[color:var(--color-text)]',
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

        <div className="mt-[var(--space-lg)] border-t border-[color:var(--color-border)] pt-[var(--space-base)]">
          <NavLink
            to={routes.home}
            className="flex items-center gap-[var(--space-sm)] rounded-[6px] px-[var(--space-sm)] py-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)] transition-colors hover:bg-[color:var(--color-surface-hover)] hover:text-[color:var(--color-text)]"
          >
            <ArrowUUpLeft size={16} weight="regular" />В студенческий режим
          </NavLink>
        </div>
      </aside>

      <main className="flex-1 overflow-x-hidden overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
