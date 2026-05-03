import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserMe } from '@/types/api'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserMe | null
  /** Поставить только токены (между login и /me — пока не подгружен user). */
  setTokens: (tokens: { access: string; refresh: string }) => void
  /** Завершить сессию: токены + загруженный профиль. */
  setSession: (tokens: { access: string; refresh: string }, user: UserMe) => void
  /** Точечно обновить профиль (после PATCH /users/me). */
  setUser: (user: UserMe) => void
  clear: () => void
}

/**
 * Стор токенов + профиля. Персистится в localStorage,
 * чтобы выжить перезагрузку вкладки.
 */
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      setTokens: (tokens) => set({ accessToken: tokens.access, refreshToken: tokens.refresh }),
      setSession: (tokens, user) =>
        set({ accessToken: tokens.access, refreshToken: tokens.refresh, user }),
      setUser: (user) => set({ user }),
      clear: () => set({ accessToken: null, refreshToken: null, user: null }),
    }),
    { name: 'la.auth' },
  ),
)
