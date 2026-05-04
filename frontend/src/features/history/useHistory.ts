import { useQuery } from '@tanstack/react-query'
import { historyApi } from './api'

export function useRecommendationHistory() {
  return useQuery({
    queryKey: ['expert', 'history'] as const,
    queryFn: () => historyApi.list(),
    staleTime: 30_000,
  })
}
