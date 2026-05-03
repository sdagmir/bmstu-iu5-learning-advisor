import { useQuery } from '@tanstack/react-query'
import { recommendationApi } from './api'

/**
 * Рекомендации текущего пользователя. Кеш-ключ совпадает с тем, что инвалидирует
 * `useProfile.patchMe.onSuccess` — после правки профиля список пересчитывается.
 */
export function useRecommendations() {
  return useQuery({
    queryKey: ['expert', 'my-recommendations'],
    queryFn: recommendationApi.getMy,
  })
}
