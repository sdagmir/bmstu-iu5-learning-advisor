import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import type { EntityConfig } from '../EntityConfig'
import type {
  AdminFocusAdvice,
  AdminFocusAdviceCreate,
} from '@/types/api'

const schema = z.object({
  discipline_id: z.string().uuid('Выбери дисциплину'),
  career_direction_id: z.string().uuid('Выбери направление'),
  focus_advice: z.string().min(1, 'Текст совета обязателен'),
  reasoning: z.string().nullable().optional(),
})

export const focusAdvicesConfig: EntityConfig<
  AdminFocusAdvice,
  AdminFocusAdviceCreate
> = {
  key: 'focus-advices',
  singular: 'фокус в дисциплине',
  pluralName: 'Фокусы в дисциплинах',
  list: adminCatalogApi.focusAdvices.list,
  create: adminCatalogApi.focusAdvices.create,
  update: adminCatalogApi.focusAdvices.update,
  delete: adminCatalogApi.focusAdvices.delete,
  columns: [
    { key: 'discipline_id', label: 'Дисциплина', mono: true, width: 220 },
    { key: 'career_direction_id', label: 'Направление', mono: true, width: 220 },
    { key: 'focus_advice', label: 'Совет' },
  ],
  fields: [
    {
      name: 'discipline_id',
      label: 'Дисциплина',
      type: 'select',
      options: async () => {
        const list = await adminCatalogApi.disciplines.list()
        return list
          .sort((a, b) => a.semester - b.semester || a.name.localeCompare(b.name))
          .map((d) => ({ value: d.id, label: `Сем ${d.semester} · ${d.name}` }))
      },
    },
    {
      name: 'career_direction_id',
      label: 'Карьерное направление',
      type: 'select',
      options: async () => {
        const list = await adminCatalogApi.careerDirections.list()
        return list.map((d) => ({ value: d.id, label: d.name }))
      },
    },
    {
      name: 'focus_advice',
      label: 'Совет',
      type: 'textarea',
      placeholder: 'Какие темы изучать глубже, какие проекты делать на курсовой.',
    },
    {
      name: 'reasoning',
      label: 'Обоснование',
      type: 'textarea',
      hint: 'Будет показано студенту в карточке рекомендации.',
    },
  ],
  schema,
  toFormValues: (row) => ({
    discipline_id: row.discipline_id,
    career_direction_id: row.career_direction_id,
    focus_advice: row.focus_advice,
    reasoning: row.reasoning,
  }),
  emptyFormValues: () => ({
    discipline_id: '',
    career_direction_id: '',
    focus_advice: '',
    reasoning: '',
  }),
  rowLabel: (row) =>
    `${row.focus_advice.slice(0, 60)}${row.focus_advice.length > 60 ? '…' : ''}`,
}
