import { Navigate } from 'react-router-dom'
import { routes } from '@/constants/routes'

/**
 * `/admin/users` — редирект на `/admin/catalog/users`. Управление
 * пользователями полностью покрыто generic CrudTable из Phase 9
 * (фильтр по статусу + PATCH role/is_active).
 */
export default function UsersPage() {
  return <Navigate to={routes.admin.catalog('users')} replace />
}
