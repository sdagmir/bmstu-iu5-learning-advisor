import { apiFetch } from '@/lib/api-client'
import type {
  AdminCKCourse,
  AdminCKCourseCreate,
  AdminCareerDirection,
  AdminCareerDirectionCreate,
  AdminCompetency,
  AdminCompetencyCreate,
  AdminDiscipline,
  AdminDisciplineCreate,
  AdminFocusAdvice,
  AdminFocusAdviceCreate,
  AdminUser,
  AdminUserUpdate,
} from '@/types/api'

/**
 * Admin-каталог CRUD. Шесть сущностей с одинаковой формой эндпоинтов
 * `/admin/{entity}`, кроме users (нет create/delete: пользователи
 * регистрируются сами через `/auth/register`).
 */

const json = (body: unknown) => ({
  method: 'POST' as const,
  body: JSON.stringify(body),
})

const patchJson = (body: unknown) => ({
  method: 'PATCH' as const,
  body: JSON.stringify(body),
})

export const adminCatalogApi = {
  competencies: {
    list: () => apiFetch<AdminCompetency[]>('/admin/competencies'),
    create: (body: AdminCompetencyCreate) =>
      apiFetch<AdminCompetency>('/admin/competencies', json(body)),
    update: (id: string, body: Partial<AdminCompetencyCreate>) =>
      apiFetch<AdminCompetency>(`/admin/competencies/${id}`, patchJson(body)),
    delete: (id: string) =>
      apiFetch<void>(`/admin/competencies/${id}`, { method: 'DELETE' }),
  },
  disciplines: {
    list: () => apiFetch<AdminDiscipline[]>('/admin/disciplines'),
    create: (body: AdminDisciplineCreate) =>
      apiFetch<AdminDiscipline>('/admin/disciplines', json(body)),
    update: (id: string, body: Partial<AdminDisciplineCreate>) =>
      apiFetch<AdminDiscipline>(`/admin/disciplines/${id}`, patchJson(body)),
    delete: (id: string) =>
      apiFetch<void>(`/admin/disciplines/${id}`, { method: 'DELETE' }),
  },
  ckCourses: {
    list: () => apiFetch<AdminCKCourse[]>('/admin/ck-courses'),
    create: (body: AdminCKCourseCreate) =>
      apiFetch<AdminCKCourse>('/admin/ck-courses', json(body)),
    update: (id: string, body: Partial<AdminCKCourseCreate>) =>
      apiFetch<AdminCKCourse>(`/admin/ck-courses/${id}`, patchJson(body)),
    delete: (id: string) =>
      apiFetch<void>(`/admin/ck-courses/${id}`, { method: 'DELETE' }),
  },
  careerDirections: {
    list: () => apiFetch<AdminCareerDirection[]>('/admin/career-directions'),
    create: (body: AdminCareerDirectionCreate) =>
      apiFetch<AdminCareerDirection>('/admin/career-directions', json(body)),
    update: (id: string, body: Partial<AdminCareerDirectionCreate>) =>
      apiFetch<AdminCareerDirection>(`/admin/career-directions/${id}`, patchJson(body)),
    delete: (id: string) =>
      apiFetch<void>(`/admin/career-directions/${id}`, { method: 'DELETE' }),
  },
  focusAdvices: {
    list: () => apiFetch<AdminFocusAdvice[]>('/admin/focus-advices'),
    create: (body: AdminFocusAdviceCreate) =>
      apiFetch<AdminFocusAdvice>('/admin/focus-advices', json(body)),
    update: (id: string, body: Partial<AdminFocusAdviceCreate>) =>
      apiFetch<AdminFocusAdvice>(`/admin/focus-advices/${id}`, patchJson(body)),
    delete: (id: string) =>
      apiFetch<void>(`/admin/focus-advices/${id}`, { method: 'DELETE' }),
  },
  users: {
    list: () => apiFetch<AdminUser[]>('/admin/users'),
    update: (id: string, body: AdminUserUpdate) =>
      apiFetch<AdminUser>(`/admin/users/${id}`, patchJson(body)),
  },
}
