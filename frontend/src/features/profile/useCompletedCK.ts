import { useCallback, useMemo } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { profileApi } from './api'
import type { CKCourse, CompletedCK } from '@/types/api'

const QUERY_KEY = ['user', 'completed-ck'] as const

/**
 * Хук для пройденных программ ЦК.
 *
 * `toggle` — стабильная ссылка через useCallback. Внутри читает текущий список
 * через `queryClient.getQueryData` (без closure на state), поэтому ссылка
 * не меняется на каждом рендере. Это позволяет memo'd CKRow корректно
 * скипать ре-рендеры при тогле соседних карточек.
 *
 * `completedSet` — Set<string> для O(1) lookup, передаётся в memo'd компоненты
 * чтобы не вычислять `.some()` на каждой строке (и чтобы prop был стабилен).
 */
export function useCompletedCK() {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: QUERY_KEY,
    queryFn: profileApi.getCompletedCK,
  })

  const completedSet = useMemo(
    () => new Set((query.data ?? []).map((c) => c.ck_course_id)),
    [query.data],
  )

  const addMut = useMutation<CompletedCK, Error, CKCourse, { prev: CompletedCK[] | undefined }>({
    mutationKey: ['profile', 'completed-ck', 'add'],
    mutationFn: (course) => profileApi.addCompletedCK(course.id),
    onMutate: (course) => {
      const prev = queryClient.getQueryData<CompletedCK[]>(QUERY_KEY)
      queryClient.setQueryData(QUERY_KEY, [
        ...(prev ?? []),
        {
          ck_course_id: course.id,
          ck_course_name: course.name,
          ck_course_category: course.category,
          completed_at: new Date().toISOString(),
        },
      ])
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(QUERY_KEY, ctx.prev)
      toast.error('Не удалось обновить пройденные ЦК. Проверь соединение.')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: ['expert', 'my-recommendations'] })
    },
  })

  const removeMut = useMutation<void, Error, string, { prev: CompletedCK[] | undefined }>({
    mutationKey: ['profile', 'completed-ck', 'remove'],
    mutationFn: (ckCourseId) => profileApi.removeCompletedCK(ckCourseId),
    onMutate: (ckCourseId) => {
      const prev = queryClient.getQueryData<CompletedCK[]>(QUERY_KEY)
      queryClient.setQueryData(
        QUERY_KEY,
        (prev ?? []).filter((c) => c.ck_course_id !== ckCourseId),
      )
      return { prev }
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) queryClient.setQueryData(QUERY_KEY, ctx.prev)
      toast.error('Не удалось обновить пройденные ЦК. Проверь соединение.')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY })
      queryClient.invalidateQueries({ queryKey: ['expert', 'my-recommendations'] })
    },
  })

  const { mutate: addMutate } = addMut
  const { mutate: removeMutate } = removeMut

  const toggle = useCallback(
    (course: CKCourse) => {
      const current = queryClient.getQueryData<CompletedCK[]>(QUERY_KEY) ?? []
      const has = current.some((c) => c.ck_course_id === course.id)
      if (has) removeMutate(course.id)
      else addMutate(course)
    },
    [queryClient, addMutate, removeMutate],
  )

  return {
    completedSet,
    isLoading: query.isLoading,
    toggle,
  }
}
