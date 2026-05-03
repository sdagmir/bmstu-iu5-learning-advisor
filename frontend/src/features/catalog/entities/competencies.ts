import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import { ALL_COMPETENCY_CATEGORIES, COMPETENCY_CATEGORY_LABELS } from '@/constants/enums'
import type { EntityConfig } from '../EntityConfig'
import type {
  AdminCompetency,
  AdminCompetencyCreate,
  CompetencyCategory,
} from '@/types/api'

const schema = z.object({
  tag: z.string().min(1, 'Тег обязателен').max(50),
  name: z.string().min(1, 'Название обязательно').max(255),
  category: z.enum(ALL_COMPETENCY_CATEGORIES as readonly [CompetencyCategory, ...CompetencyCategory[]]),
})

export const competenciesConfig: EntityConfig<AdminCompetency, AdminCompetencyCreate> = {
  key: 'competencies',
  singular: 'компетенцию',
  pluralName: 'Компетенции',
  list: adminCatalogApi.competencies.list,
  create: adminCatalogApi.competencies.create,
  update: adminCatalogApi.competencies.update,
  delete: adminCatalogApi.competencies.delete,
  columns: [
    { key: 'tag', label: 'Тег', mono: true, width: 140 },
    { key: 'name', label: 'Название' },
    {
      key: 'category',
      label: 'Категория',
      width: 200,
      render: (row) => COMPETENCY_CATEGORY_LABELS[row.category],
    },
  ],
  fields: [
    {
      name: 'tag',
      label: 'Тег',
      type: 'text',
      placeholder: 'PROG-101',
      hint: 'Короткий читаемый идентификатор. Используется в правилах ЭС.',
    },
    { name: 'name', label: 'Название', type: 'text' },
    {
      name: 'category',
      label: 'Категория',
      type: 'select',
      options: ALL_COMPETENCY_CATEGORIES.map((c) => ({
        value: c,
        label: COMPETENCY_CATEGORY_LABELS[c],
      })),
    },
  ],
  schema,
  toFormValues: (row) => ({ tag: row.tag, name: row.name, category: row.category }),
  emptyFormValues: () => ({ tag: '', name: '', category: 'programming' }),
  rowLabel: (row) => `${row.tag} · ${row.name}`,
}
