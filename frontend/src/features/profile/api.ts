import { apiFetch } from '@/lib/api-client'
import type {
  CompletedCK,
  GradePut,
  GradeRead,
  ProfileUpdate,
  UserMe,
} from '@/types/api'

export const profileApi = {
  getMe: () => apiFetch<UserMe>('/users/me'),

  patchMe: (body: ProfileUpdate) =>
    apiFetch<UserMe>('/users/me', { method: 'PATCH', body: JSON.stringify(body) }),

  // --- Grades ---
  getGrades: () => apiFetch<GradeRead[]>('/users/me/grades'),

  /** PUT — full replace. Передавать ВСЕ оценки сразу, не diff. */
  putGrades: (grades: GradePut[]) =>
    apiFetch<GradeRead[]>('/users/me/grades', {
      method: 'PUT',
      body: JSON.stringify({ grades }),
    }),

  // --- Completed CK ---
  getCompletedCK: () => apiFetch<CompletedCK[]>('/users/me/completed-ck'),

  addCompletedCK: (ck_course_id: string) =>
    apiFetch<CompletedCK>('/users/me/completed-ck', {
      method: 'POST',
      body: JSON.stringify({ ck_course_id }),
    }),

  removeCompletedCK: (ck_course_id: string) =>
    apiFetch<void>(`/users/me/completed-ck/${ck_course_id}`, { method: 'DELETE' }),
}
