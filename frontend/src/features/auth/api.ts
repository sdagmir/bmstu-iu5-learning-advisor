import { apiFetch } from '@/lib/api-client'
import type {
  LoginRequest,
  RegisterRequest,
  RefreshRequest,
  TokenPair,
  UserMe,
} from '@/types/api'

export const authApi = {
  register: (body: RegisterRequest) =>
    apiFetch<TokenPair>('/auth/register', { method: 'POST', body: JSON.stringify(body) }),

  login: (body: LoginRequest) =>
    apiFetch<TokenPair>('/auth/login', { method: 'POST', body: JSON.stringify(body) }),

  /**
   * Демо-логин для защиты диплома. На бэке активен только при
   * `DEMO_ACCOUNT_ENABLED=true` — иначе возвращается 404. Фронт
   * показывает кнопку всегда и тихо обрабатывает ошибку.
   */
  demoLogin: () => apiFetch<TokenPair>('/auth/demo-login', { method: 'POST' }),

  refresh: (body: RefreshRequest) =>
    apiFetch<TokenPair>('/auth/refresh', { method: 'POST', body: JSON.stringify(body) }),

  logout: (refresh_token: string) =>
    apiFetch<void>('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token } satisfies RefreshRequest),
    }),

  me: () => apiFetch<UserMe>('/users/me'),
}
