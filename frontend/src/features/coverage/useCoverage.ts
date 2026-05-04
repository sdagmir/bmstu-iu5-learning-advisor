import { useQuery } from '@tanstack/react-query'
import { coverageApi } from './api'

export function useCoverage() {
  return useQuery({
    queryKey: ['users', 'me', 'coverage'] as const,
    queryFn: coverageApi.me,
    staleTime: 30_000,
  })
}
