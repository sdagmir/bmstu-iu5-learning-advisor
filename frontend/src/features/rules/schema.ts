import { z } from 'zod'
import { ALL_RULE_GROUPS } from '@/constants/enums'
import type { RecommendationCategory, RecommendationPriority, RuleGroup } from '@/types/api'

const RULE_GROUP_VALUES = ALL_RULE_GROUPS as readonly RuleGroup[]

/**
 * Атом условия — `{ param, op, value }`. Бэк допускает свободный JSON,
 * но фронт-эксперт получает осмысленный линт через эту форму.
 */
const opSchema = z.enum([
  'eq',
  'neq',
  'gt',
  'gte',
  'lt',
  'lte',
  'in',
  'not_in',
  'lookup_eq',
  'lookup_neq',
])

/**
 * Условие — рекурсивная структура: `{all: [...]}`, `{any: [...]}`, либо атом.
 * z.lazy чтобы поддержать вложенные группы.
 */
export const conditionSchema: z.ZodType<unknown> = z.lazy(() =>
  z.union([
    z.object({ all: z.array(conditionSchema) }).strict(),
    z.object({ any: z.array(conditionSchema) }).strict(),
    z
      .object({
        param: z.string().min(1),
        op: opSchema,
        value: z.unknown(),
      })
      .strict(),
  ]),
)

/** Валидация рекомендации-шаблона. Минимум: category, title, priority, reasoning. */
export const recommendationSchema = z
  .object({
    category: z.enum([
      'ck_course',
      'technopark',
      'focus',
      'coursework',
      'warning',
      'strategy',
    ]),
    title: z.string().min(1, 'Заголовок обязателен'),
    priority: z.enum(['high', 'medium', 'low']),
    reasoning: z.string().min(1, 'Обоснование обязательно'),
  })
  .passthrough()

/**
 * Структурированная форма шаблона рекомендации — заменила сырое JSON-поле.
 * Из всех 57 правил в `rules_data.py` используется ровно 5 ключей, поэтому
 * сделать билдер было безопасно без JSON-fallback. `competencyGap` пустая
 * строка трактуется как «не передавать» — собирается в JSON только если есть.
 */
const REC_CATEGORY_VALUES = [
  'ck_course',
  'technopark',
  'focus',
  'coursework',
  'warning',
  'strategy',
] as const satisfies readonly RecommendationCategory[]

const REC_PRIORITY_VALUES = ['high', 'medium', 'low'] as const satisfies readonly RecommendationPriority[]

export const recommendationFormSchema = z.object({
  category: z.enum(REC_CATEGORY_VALUES),
  title: z.string().min(1, 'Заголовок обязателен').max(500),
  priority: z.enum(REC_PRIORITY_VALUES),
  reasoning: z.string().min(1, 'Обоснование обязательно'),
  /** UID компетенции из радара (например `ml_basics`). Пустая строка = не передавать. */
  competencyGap: z.string(),
})

export type RecommendationFormValues = z.infer<typeof recommendationFormSchema>

/** Главная схема для react-hook-form. condition пока JSON (этап 3), recommendation — builder. */
export const ruleFormSchema = z.object({
  number: z.number().int().min(1, 'Номер должен быть ≥ 1'),
  group: z.enum(RULE_GROUP_VALUES as [RuleGroup, ...RuleGroup[]]),
  name: z.string().min(1, 'Название обязательно').max(255),
  description: z.string(),
  conditionJson: z
    .string()
    .min(1, 'Условие обязательно')
    .superRefine((str, ctx) => {
      let parsed: unknown
      try {
        parsed = JSON.parse(str)
      } catch (e) {
        ctx.addIssue({ code: 'custom', message: 'Неверный JSON: ' + (e as Error).message })
        return
      }
      const result = conditionSchema.safeParse(parsed)
      if (!result.success) {
        const firstErr = result.error.issues[0]
        const msg = firstErr ? `${firstErr.path.join('.') || 'root'}: ${firstErr.message}` : 'Структура условия некорректна'
        ctx.addIssue({ code: 'custom', message: msg })
      }
    }),
  recommendation: recommendationFormSchema,
  priority: z.number().int(),
  is_active: z.boolean(),
})

export type RuleFormValues = z.infer<typeof ruleFormSchema>

/** Безопасный JSON.stringify(.., null, 2) — для печати в textarea. */
export function stringifyJson(value: unknown): string {
  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return ''
  }
}

/** Парсит JSON, считая пустую строку пустым объектом. Бросает SyntaxError. */
export function parseJsonObject(str: string): Record<string, unknown> {
  const parsed = JSON.parse(str)
  if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
    throw new Error('Ожидался объект')
  }
  return parsed as Record<string, unknown>
}

/**
 * 5 уровней приоритета правила — bucket-значения 0..100 с шагом 25.
 * Sparse (не 1..5), чтобы при необходимости можно было вставить промежуточные
 * без миграции БД. При загрузке существующих правил с произвольным числом —
 * округляем к ближайшему bucket (см. `priorityToBucket`).
 */
export const PRIORITY_LEVELS = [
  { value: 100, label: 'Высочайший', hint: 'выводится первым' },
  { value: 75, label: 'Высокий', hint: 'выше обычного' },
  { value: 50, label: 'Обычный', hint: 'базовый уровень' },
  { value: 25, label: 'Низкий', hint: 'ниже обычного' },
  { value: 0, label: 'Минимальный', hint: 'выводится последним' },
] as const

const PRIORITY_VALUES = PRIORITY_LEVELS.map((l) => l.value)

/** Ближайший bucket к произвольному числу — для legacy-данных. */
export function priorityToBucket(n: number): number {
  return PRIORITY_VALUES.reduce((closest, current) =>
    Math.abs(current - n) < Math.abs(closest - n) ? current : closest,
  )
}

/**
 * Стартовое значение для нового правила: пустая `all`-группа +
 * минимально-валидный шаблон рекомендации. Для онбординга «как это выглядит».
 */
export const NEW_RULE_DEFAULTS = {
  number: 1,
  group: 'basic_universal' as RuleGroup,
  name: '',
  description: '',
  conditionJson: stringifyJson({ all: [] }),
  recommendation: {
    category: 'strategy',
    title: '',
    priority: 'medium',
    reasoning: '',
    competencyGap: '',
  },
  priority: 50,
  is_active: true,
} satisfies RuleFormValues

/**
 * Из формы → API: чистим пустой competencyGap (не отправляем) и переименовываем
 * camelCase → snake_case под `competency_gap` контракт бэка.
 */
export function buildRecommendation(form: RecommendationFormValues): Record<string, unknown> {
  const out: Record<string, unknown> = {
    category: form.category,
    title: form.title,
    priority: form.priority,
    reasoning: form.reasoning,
  }
  const gap = form.competencyGap.trim()
  if (gap) out.competency_gap = gap
  return out
}

/**
 * API → форма: раскладываем существующий recommendation объект на поля формы.
 * Неизвестные поля игнорируем (из аудита 57 правил — таких нет в реальности).
 */
export function parseRecommendation(value: unknown): RecommendationFormValues {
  const obj = (value && typeof value === 'object' ? (value as Record<string, unknown>) : {})
  const cat = obj.category as RecommendationCategory | undefined
  const pri = obj.priority as RecommendationPriority | undefined
  return {
    category: cat && REC_CATEGORY_VALUES.includes(cat) ? cat : 'strategy',
    title: typeof obj.title === 'string' ? obj.title : '',
    priority: pri && REC_PRIORITY_VALUES.includes(pri) ? pri : 'medium',
    reasoning: typeof obj.reasoning === 'string' ? obj.reasoning : '',
    competencyGap:
      obj.competency_gap == null ? '' : String(obj.competency_gap),
  }
}
