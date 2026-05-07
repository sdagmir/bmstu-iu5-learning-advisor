import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import { CK_CATEGORY_LABELS } from '@/constants/enums'
import type { EntityConfig } from '../EntityConfig'
import type {
  AdminCKCourse,
  AdminCKCourseCreate,
  CKCourseCategory,
} from '@/types/api'

const ALL_CK_CATEGORIES = [
  'ml',
  'development',
  'security',
  'testing',
  'management',
  'other',
] as const satisfies readonly CKCourseCategory[]

const schema = z.object({
  name: z.string().min(1, 'Название обязательно').max(255),
  description: z.string().nullable(),
  category: z.enum(ALL_CK_CATEGORIES),
  credits: z.number().int().min(1),
  competency_ids: z.array(z.string()),
  prerequisite_ids: z.array(z.string()),
})

export const ckCoursesConfig: EntityConfig<AdminCKCourse, AdminCKCourseCreate> = {
  key: 'ck-courses',
  singular: 'программу ЦК',
  pluralName: 'Программы ЦК',
  list: adminCatalogApi.ckCourses.list,
  create: adminCatalogApi.ckCourses.create,
  update: adminCatalogApi.ckCourses.update,
  delete: adminCatalogApi.ckCourses.delete,
  columns: [
    { key: 'name', label: 'Название' },
    {
      key: 'category',
      label: 'Категория',
      width: 180,
      render: (row) => CK_CATEGORY_LABELS[row.category] ?? '—',
    },
    { key: 'credits', label: 'ЕЗ', mono: true, width: 60 },
    {
      key: 'competencies',
      label: 'Закрывает',
      width: 120,
      render: (row) => `${row.competencies?.length ?? 0} шт`,
    },
    {
      key: 'prerequisites',
      label: 'Prereq',
      width: 100,
      render: (row) => `${row.prerequisites?.length ?? 0} шт`,
    },
  ],
  fields: [
    { name: 'name', label: 'Название', type: 'text' },
    {
      name: 'description',
      label: 'Описание',
      type: 'textarea',
    },
    {
      name: 'category',
      label: 'Категория',
      type: 'select',
      options: ALL_CK_CATEGORIES.map((c) => ({
        value: c,
        label: CK_CATEGORY_LABELS[c],
      })),
    },
    {
      name: 'credits',
      label: 'Единицы занятости',
      type: 'number',
    },
    {
      name: 'competency_ids',
      label: 'Закрывает компетенции',
      type: 'multiselect',
      options: async () => {
        const list = await adminCatalogApi.competencies.list()
        return list.map((c) => ({ value: c.id, label: `${c.tag} · ${c.name}` }))
      },
    },
    {
      name: 'prerequisite_ids',
      label: 'Требует на входе',
      type: 'multiselect',
      hint: 'Компетенции, которые должны быть до начала курса.',
      options: async () => {
        const list = await adminCatalogApi.competencies.list()
        return list.map((c) => ({ value: c.id, label: `${c.tag} · ${c.name}` }))
      },
    },
  ],
  schema,
  toFormValues: (row) => ({
    name: row.name,
    description: row.description,
    category: row.category,
    credits: row.credits,
    competency_ids: row.competencies?.map((c) => c.id) ?? [],
    prerequisite_ids: row.prerequisites?.map((c) => c.id) ?? [],
  }),
  emptyFormValues: () => ({
    name: '',
    description: '',
    category: 'development',
    credits: 2,
    competency_ids: [],
    prerequisite_ids: [],
  }),
  rowLabel: (row) => row.name,
}
