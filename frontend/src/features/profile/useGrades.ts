import { useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { profileApi } from './api'
import type { GradeRead } from '@/types/api'

const QUERY_KEY = ['user', 'grades'] as const
const MUTATION_KEY = ['profile', 'grades'] as const

/**
 * Хук для оценок по дисциплинам. PUT — full replace, поэтому setGrade
 * формирует новый массив и шлёт целиком. Optimistic-апдейт через onMutate.
 *
 * `setGrade` — СТАБИЛЬНАЯ ссылка через useCallback. Внутри читает текущие
 * grades через `queryClient.getQueryData` (без closure на query.data),
 * поэтому ссылка не меняется на каждом рендере. Это позволяет потребителям
 * (memo'd GradeRow) корректно скипать ре-рендеры.
 */
export function useGrades() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: profileApi.getGrades,
  })

  const putMut = useMutation<GradeRead[], Error, GradeRead[], { prev: GradeRead[] | undefined }>({
    mutationKey: MUTATION_KEY,
    mutationFn: (next) =>
      profileApi.putGrades(next.map((g) => ({ discipline_id: g.discipline_id, grade: g.grade }))),
    onMutate: (next) => {
      const prev = queryClient.getQueryData<GradeRead[]>(QUERY_KEY)
      queryClient.setQueryData(QUERY_KEY, next)
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(QUERY_KEY, ctx.prev)
      toast.error('Не удалось сохранить оценку. Проверь соединение.')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: ['expert', 'my-recommendations'] })
    },
  })

  const { mutate } = putMut

  const setGrade = useCallback(
    (disciplineId: string, disciplineName: string, grade: number | null) => {
      const current = queryClient.getQueryData<GradeRead[]>(QUERY_KEY) ?? []
      const others = current.filter((g) => g.discipline_id !== disciplineId)
      const next: GradeRead[] =
        grade === null
          ? others
          : [
              ...others,
              { discipline_id: disciplineId, discipline_name: disciplineName, grade },
            ]
      mutate(next)
    },
    [queryClient, mutate],
  )

  return {
    grades: query.data ?? [],
    isLoading: query.isLoading,
    setGrade,
  }
}
