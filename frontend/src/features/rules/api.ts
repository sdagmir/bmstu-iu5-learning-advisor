import { apiFetch } from '@/lib/api-client'
import type {
  Rule,
  RuleCreate,
  RuleEditingLockStatus,
  RulePreviewRequest,
  RulePreviewResponse,
  RuleUpdate,
} from '@/types/api'

/**
 * Тонкая обёртка над `/admin/rules/**`. Lock и preview — отдельные ветки,
 * чтобы UI собирал их через узкоспециализированные хуки.
 */
export const rulesApi = {
  list: () => apiFetch<Rule[]>('/admin/rules'),
  get: (id: string) => apiFetch<Rule>(`/admin/rules/${id}`),
  create: (body: RuleCreate) =>
    apiFetch<Rule>('/admin/rules', { method: 'POST', body: JSON.stringify(body) }),
  update: (id: string, body: RuleUpdate) =>
    apiFetch<Rule>(`/admin/rules/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  delete: (id: string) => apiFetch<void>(`/admin/rules/${id}`, { method: 'DELETE' }),
  publish: (id: string) =>
    apiFetch<Rule>(`/admin/rules/${id}/publish`, { method: 'POST' }),
  unpublish: (id: string) =>
    apiFetch<Rule>(`/admin/rules/${id}/unpublish`, { method: 'POST' }),
  preview: (body: RulePreviewRequest) =>
    apiFetch<RulePreviewResponse>('/admin/rules/preview', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  lock: {
    status: () => apiFetch<RuleEditingLockStatus>('/admin/rules/lock'),
    acquire: () =>
      apiFetch<RuleEditingLockStatus>('/admin/rules/lock', { method: 'POST' }),
    release: () => apiFetch<void>('/admin/rules/lock', { method: 'DELETE' }),
    forceRelease: () => apiFetch<void>('/admin/rules/lock/force', { method: 'DELETE' }),
  },
}
