import { apiFetch } from '@/lib/api-client'
import type { CKCourse, Discipline } from '@/types/api'

export const catalogApi = {
  /** Дисциплины из учебного плана. semesterMax фильтрует по семестру (включительно). */
  getDisciplines: (semesterMax?: number) => {
    const query = semesterMax !== undefined ? `?semester_max=${semesterMax}` : ''
    return apiFetch<Discipline[]>(`/catalog/disciplines${query}`)
  },

  /** Программы цифровой кафедры — для чеклиста пройденных. */
  getCkCourses: () => apiFetch<CKCourse[]>('/catalog/ck-courses'),
}
