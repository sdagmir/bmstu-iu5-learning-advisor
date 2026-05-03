import { Navigate } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuthStore } from '@/stores/authStore'
import { routes } from '@/constants/routes'

/**
 * Guards используют узкий селектор по `role` — примитив, Zustand сравнивает по `===`.
 * При обновлении любого ДРУГОГО поля профиля (semester, career_goal и т.п.) гарды
 * НЕ ре-рендерятся → cascade-перерисовки шеллов и страниц не происходит.
 */

/** Требуется любая аутентификация. Иначе — на /login. */
export function RequireAuth({ children }: { children: ReactNode }) {
  const role = useAuthStore((s) => s.user?.role ?? null)
  if (role === null) return <Navigate to={routes.login} replace />
  return children
}

/** Требуется роль admin. Иначе — на / (если авторизован) или /login. */
export function RequireAdmin({ children }: { children: ReactNode }) {
  const role = useAuthStore((s) => s.user?.role ?? null)
  if (role === null) return <Navigate to={routes.login} replace />
  if (role !== 'admin') return <Navigate to={routes.home} replace />
  return children
}

/** Если уже авторизован — редирект с /login, /register на /. */
export function RedirectIfAuth({ children }: { children: ReactNode }) {
  const role = useAuthStore((s) => s.user?.role ?? null)
  if (role !== null) return <Navigate to={routes.home} replace />
  return children
}
