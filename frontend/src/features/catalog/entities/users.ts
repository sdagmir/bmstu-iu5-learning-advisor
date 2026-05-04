import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import {
  ALL_USER_ROLES,
  CAREER_GOAL_LABELS,
  USER_ROLE_LABELS,
} from '@/constants/enums'
import type { EntityConfig } from '../EntityConfig'
import type { AdminUser, AdminUserUpdate, UserRole } from '@/types/api'

const schema = z.object({
  role: z.enum(ALL_USER_ROLES as readonly [UserRole, ...UserRole[]]).optional(),
  is_active: z.boolean().optional(),
})

/**
 * Особенный конфиг: только список + update. Пользователи регистрируются
 * сами через `/auth/register` — create в admin-режиме не предусмотрен.
 * Удалять тоже нельзя — только `is_active = false` (кнопка-свитч в форме).
 */
export const usersConfig: EntityConfig<AdminUser, AdminUserUpdate> = {
  key: 'users',
  singular: 'пользователя',
  pluralName: 'Пользователи',
  list: adminCatalogApi.users.list,
  update: adminCatalogApi.users.update,
  // create / delete intentionally omitted
  columns: [
    { key: 'email', label: 'Email', width: 280 },
    {
      key: 'role',
      label: 'Роль',
      width: 140,
      render: (row) => USER_ROLE_LABELS[row.role] ?? '—',
    },
    {
      key: 'is_active',
      label: 'Активен',
      width: 100,
      render: (row) => (row.is_active ? 'Да' : 'Нет'),
    },
    {
      key: 'career_goal',
      label: 'Цель',
      render: (row) =>
        row.career_goal ? CAREER_GOAL_LABELS[row.career_goal] : '—',
    },
    { key: 'semester', label: 'Сем', mono: true, width: 60 },
  ],
  fields: [
    {
      name: 'role',
      label: 'Роль',
      type: 'select',
      options: ALL_USER_ROLES.map((r) => ({ value: r, label: USER_ROLE_LABELS[r] })),
    },
    {
      name: 'is_active',
      label: 'Активен',
      type: 'switch',
      hint: 'Выключенный пользователь не сможет залогиниться.',
    },
  ],
  schema,
  toFormValues: (row) => ({ role: row.role, is_active: row.is_active }),
  emptyFormValues: () => ({}),
  rowLabel: (row) => row.email,
}
