import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { profileApi } from './api'
import { useAuthStore } from '@/stores/authStore'
import type { ProfileUpdate, UserMe } from '@/types/api'

/**
 * Только МУТАЦИЯ профиля. Чтение — потребители подписываются на нужные поля
 * `useAuthStore` напрямую (узкими селекторами), чтобы не ре-рендериться на
 * правке соседних полей. Этот хук не возвращает `profile` намеренно.
 */
export function useProfile() {
  const setUser = useAuthStore((s) => s.setUser)
  const queryClient = useQueryClient()

  const patchMe = useMutation<UserMe, Error, ProfileUpdate, { prev: UserMe | null }>({
    mutationKey: ['profile', 'me'],
    mutationFn: profileApi.patchMe,
    onMutate: (update) => {
      // Optimistic-апдейт: моментально применяем изменения локально,
      // чтобы радио/селекты «откликались мгновенно». На ошибку откатимся.
      const prev = useAuthStore.getState().user
      if (prev) setUser({ ...prev, ...update })
      return { prev }
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) setUser(context.prev)
      toast.error('Не удалось сохранить изменения. Проверь соединение.')
    },
    onSuccess: () => {
      // НЕ дублируем setUser — оптимистичное состояние уже корректно (бэк возвращает
      // те же поля что мы послали). Двойной setUser создавал второй ререндер
      // и визуальное мерцание. Кеш профиля просто инвалидируем для свежести.
      queryClient.invalidateQueries({ queryKey: ['user', 'me'] })
      queryClient.invalidateQueries({ queryKey: ['expert', 'my-recommendations'] })
    },
  })

  return { patchMe }
}

/** Минимально достаточный профиль для рекомендаций — все четыре X1–X4. */
export function isProfileMinimallyComplete(u: UserMe | null): boolean {
  if (!u) return false
  return Boolean(
    u.career_goal &&
      u.semester !== null &&
      u.technopark_status !== null &&
      u.workload_pref !== null,
  )
}
