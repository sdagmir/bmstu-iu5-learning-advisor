import { useQuery } from '@tanstack/react-query'
import { historyApi } from './api'

export function useRecommendationHistory() {
  return useQuery({
    queryKey: ['expert', 'history'] as const,
    queryFn: () => historyApi.list(),
    // Каждый заход на /history = свежий fetch. 30s кеш создавал race
    // с invalidate из PATCH профиля — раз через раз показывало старое.
    staleTime: 0,
  })
}
