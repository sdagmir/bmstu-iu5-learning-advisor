import { useQuery } from '@tanstack/react-query'
import { coverageApi } from './api'
import { useAuthStore } from '@/stores/authStore'

/**
 * Покрытие компетенций для текущего студента. Если карьерная цель не
 * выбрана (`career_goal` === null или `'undecided'`), бэк всё равно вернёт
 * пустой ответ — но на фронте мы отрисовываем early-return на CoveragePage,
 * поэтому экономим запрос через `enabled` guard.
 */
export function useCoverage() {
  const careerGoal = useAuthStore((s) => s.user?.career_goal ?? null)
  const enabled = !!careerGoal && careerGoal !== 'undecided'
  return useQuery({
    queryKey: ['users', 'me', 'coverage'] as const,
    queryFn: coverageApi.me,
    staleTime: 30_000,
    enabled,
  })
}
