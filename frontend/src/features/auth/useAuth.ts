import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { authApi } from './api'
import { useAuthStore } from '@/stores/authStore'
import { routes } from '@/constants/routes'
import type { LoginRequest, RegisterRequest, TokenPair, UserMe } from '@/types/api'

/**
 * X1–X4 заданы → можно показывать рекомендации, минуем онбординг.
 * Соответствует требованию плана: «isComplete — все X1–X4 заданы».
 */
function isProfileMinimallyComplete(u: UserMe): boolean {
  return Boolean(
    u.career_goal &&
      u.semester !== null &&
      u.technopark_status !== null &&
      u.workload_pref !== null,
  )
}

/**
 * Хук-фасад над auth-flow: login / register / logout.
 * Нюанс: между получением токенов и загрузкой /users/me мы уже знаем токены,
 * но ещё не знаем user'а. Поэтому ставим токены через `setTokens`, чтобы
 * apiFetch смог авторизовать запрос к /me, и только потом фиксируем сессию.
 */
export function useAuth() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const setTokens = useAuthStore((s) => s.setTokens)
  const setSession = useAuthStore((s) => s.setSession)
  const clear = useAuthStore((s) => s.clear)

  async function completeAuth(tokens: TokenPair): Promise<UserMe> {
    setTokens({ access: tokens.access_token, refresh: tokens.refresh_token })
    try {
      const user = await authApi.me()
      setSession({ access: tokens.access_token, refresh: tokens.refresh_token }, user)
      return user
    } catch (err) {
      // Если /me не отдал юзера — откатываем токены, чтобы guard'ы не пустили
      // в систему «полу-залогиненного» пользователя без профиля.
      clear()
      throw err
    }
  }

  const login = useMutation({
    mutationFn: async (body: LoginRequest) => {
      const tokens = await authApi.login(body)
      return await completeAuth(tokens)
    },
    onSuccess: (user) => {
      navigate(isProfileMinimallyComplete(user) ? routes.home : routes.onboarding, {
        replace: true,
      })
    },
  })

  const register = useMutation({
    mutationFn: async (body: RegisterRequest) => {
      const tokens = await authApi.register(body)
      return await completeAuth(tokens)
    },
    onSuccess: () => {
      // Только что созданный аккаунт — профиль гарантированно пустой.
      navigate(routes.onboarding, { replace: true })
    },
  })

  const logout = useMutation({
    mutationFn: async () => {
      const refresh = useAuthStore.getState().refreshToken
      if (refresh) {
        try {
          await authApi.logout(refresh)
        } catch {
          // Лог-аут локальный должен сработать даже если бэк недоступен.
        }
      }
    },
    onSettled: () => {
      clear()
      queryClient.clear()
      navigate(routes.login, { replace: true })
    },
  })

  return { login, register, logout }
}
