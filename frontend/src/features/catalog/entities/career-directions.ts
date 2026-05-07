import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import type { EntityConfig } from '../EntityConfig'
import type {
  AdminCareerDirection,
  AdminCareerDirectionCreate,
} from '@/types/api'

const schema = z.object({
  name: z.string().min(1, 'Название обязательно').max(100),
  description: z.string().nullable(),
  example_jobs: z.string().nullable(),
  competency_ids: z.array(z.string()),
})

export const careerDirectionsConfig: EntityConfig<
  AdminCareerDirection,
  AdminCareerDirectionCreate
> = {
  key: 'career-directions',
  singular: 'карьерное направление',
  pluralName: 'Карьерные направления',
  list: adminCatalogApi.careerDirections.list,
  create: adminCatalogApi.careerDirections.create,
  update: adminCatalogApi.careerDirections.update,
  delete: adminCatalogApi.careerDirections.delete,
  columns: [
    { key: 'name', label: 'Название', width: 220 },
    {
      key: 'description',
      label: 'Описание',
      render: (row) => row.description ?? '—',
    },
    {
      key: 'competencies',
      label: 'Целевые компетенции',
      width: 180,
      render: (row) => `${row.competencies?.length ?? 0} шт`,
    },
  ],
  fields: [
    { name: 'name', label: 'Название', type: 'text', placeholder: 'Backend-разработка' },
    {
      name: 'description',
      label: 'Описание',
      type: 'textarea',
      hint: 'Что делает специалист этого направления.',
    },
    {
      name: 'example_jobs',
      label: 'Примеры должностей',
      type: 'textarea',
      placeholder: 'Backend-разработчик в Yandex, Avito',
    },
    {
      name: 'competency_ids',
      label: 'Целевые компетенции',
      type: 'multiselect',
      hint: 'Используются в radar coverage студентов.',
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
    example_jobs: row.example_jobs,
    competency_ids: row.competencies?.map((c) => c.id) ?? [],
  }),
  emptyFormValues: () => ({
    name: '',
    description: '',
    example_jobs: '',
    competency_ids: [],
  }),
  rowLabel: (row) => row.name,
}
