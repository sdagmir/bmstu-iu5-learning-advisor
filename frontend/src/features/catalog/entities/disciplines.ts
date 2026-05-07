import { z } from 'zod'
import { adminCatalogApi } from '../adminApi'
import {
  ALL_DISCIPLINE_TYPES,
  DISCIPLINE_TYPE_LABELS,
} from '@/constants/enums'
import type { EntityConfig } from '../EntityConfig'
import type {
  AdminDiscipline,
  AdminDisciplineCreate,
  DisciplineType,
} from '@/types/api'

const schema = z.object({
  name: z.string().min(1, 'Название обязательно').max(255),
  semester: z.number().int().min(1, '1–8').max(8, '1–8'),
  credits: z.number().int().min(1, 'Не меньше 1'),
  type: z.enum(ALL_DISCIPLINE_TYPES as readonly [DisciplineType, ...DisciplineType[]]),
  control_form: z.string().min(1, 'Форма контроля обязательна').max(50),
  department: z.string().nullable(),
  competency_ids: z.array(z.string()),
})

export const disciplinesConfig: EntityConfig<AdminDiscipline, AdminDisciplineCreate> = {
  key: 'disciplines',
  singular: 'дисциплину',
  pluralName: 'Дисциплины',
  list: adminCatalogApi.disciplines.list,
  create: adminCatalogApi.disciplines.create,
  update: adminCatalogApi.disciplines.update,
  delete: adminCatalogApi.disciplines.delete,
  columns: [
    { key: 'semester', label: 'Сем', mono: true, width: 60 },
    { key: 'name', label: 'Название' },
    {
      key: 'type',
      label: 'Тип',
      width: 140,
      render: (row) => DISCIPLINE_TYPE_LABELS[row.type] ?? '—',
    },
    { key: 'credits', label: 'ЕЗ', mono: true, width: 60 },
    {
      key: 'competencies',
      label: 'Компетенции',
      width: 140,
      render: (row) => `${row.competencies?.length ?? 0} шт`,
    },
  ],
  fields: [
    { name: 'name', label: 'Название', type: 'text' },
    {
      name: 'semester',
      label: 'Семестр',
      type: 'number',
      hint: '1–8',
    },
    {
      name: 'credits',
      label: 'Единицы занятости',
      type: 'number',
    },
    {
      name: 'type',
      label: 'Тип',
      type: 'select',
      options: ALL_DISCIPLINE_TYPES.map((t) => ({
        value: t,
        label: DISCIPLINE_TYPE_LABELS[t],
      })),
    },
    {
      name: 'control_form',
      label: 'Форма контроля',
      type: 'text',
      placeholder: 'Зачёт / Экзамен / Курсовая',
    },
    {
      name: 'department',
      label: 'Кафедра',
      type: 'text',
      placeholder: 'ИУ5',
    },
    {
      name: 'competency_ids',
      label: 'Компетенции',
      type: 'multiselect',
      hint: 'Какие компетенции закрывает дисциплина. Используется в radar.',
      options: async () => {
        const competencies = await adminCatalogApi.competencies.list()
        return competencies.map((c) => ({ value: c.id, label: `${c.tag} · ${c.name}` }))
      },
    },
  ],
  schema,
  toFormValues: (row) => ({
    name: row.name,
    semester: row.semester,
    credits: row.credits,
    type: row.type,
    control_form: row.control_form,
    department: row.department,
    competency_ids: row.competencies?.map((c) => c.id) ?? [],
  }),
  emptyFormValues: () => ({
    name: '',
    semester: 1,
    credits: 3,
    type: 'mandatory',
    control_form: '',
    department: null,
    competency_ids: [],
  }),
  rowLabel: (row) => row.name,
}
