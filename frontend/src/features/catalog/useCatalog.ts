import { useQuery } from '@tanstack/react-query'
import { catalogApi } from './api'

/** Кэшируем каталог надолго — он почти не меняется (раз в семестр на бэке). */
const CATALOG_STALE_TIME = 5 * 60 * 1000 // 5 минут

export function useDisciplines(semesterMax?: number) {
  return useQuery({
    queryKey: ['catalog', 'disciplines', { semesterMax: semesterMax ?? null }],
    queryFn: () => catalogApi.getDisciplines(semesterMax),
    staleTime: CATALOG_STALE_TIME,
  })
}

export function useCkCourses() {
  return useQuery({
    queryKey: ['catalog', 'ck-courses'],
    queryFn: catalogApi.getCkCourses,
    staleTime: CATALOG_STALE_TIME,
  })
}
