import { Navigate, useLocation } from 'react-router-dom'
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

/**
 * Студент с незаполненным минимальным профилем (X1–X4: career_goal, semester,
 * technopark_status, workload_pref) принудительно держится на /onboarding.
 * Без этих полей весь продукт бесполезен (ЭС не выдаст рекомендации, чат
 * не знает контекста). После заполнения — редирект с /onboarding на /home,
 * чтобы не давать «переонбордиться» через прямой URL (для правок есть /profile).
 *
 * Селектор возвращает boolean — узкий примитив, перерендер только когда
 * меняется именно полнота профиля, а не любое поле user.
 */
export function RequireStudentProfile({ children }: { children: ReactNode }) {
  const role = useAuthStore((s) => s.user?.role ?? null)
  const isComplete = useAuthStore((s) => {
    const u = s.user
    if (!u || u.role !== 'student') return true
    return Boolean(
      u.career_goal &&
        u.semester !== null &&
        u.technopark_status !== null &&
        u.workload_pref !== null,
    )
  })
  const onOnboarding = useLocation().pathname.endsWith('/onboarding')

  // Не студент (admin) — пропускаем проверку
  if (role !== 'student') return children
  if (!isComplete && !onOnboarding) return <Navigate to={routes.onboarding} replace />
  if (isComplete && onOnboarding) return <Navigate to={routes.home} replace />
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
