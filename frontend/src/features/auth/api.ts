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

  refresh: (body: RefreshRequest) =>
    apiFetch<TokenPair>('/auth/refresh', { method: 'POST', body: JSON.stringify(body) }),

  logout: (refresh_token: string) =>
    apiFetch<void>('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token } satisfies RefreshRequest),
    }),

  me: () => apiFetch<UserMe>('/users/me'),
}
