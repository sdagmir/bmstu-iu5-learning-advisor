import { z } from 'zod'
import { ALL_RULE_GROUPS } from '@/constants/enums'
import type { RuleGroup } from '@/types/api'

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

/** Главная схема для react-hook-form. JSON-поля приходят как строки и парсятся. */
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
  recommendationJson: z
    .string()
    .min(1, 'Шаблон рекомендации обязателен')
    .superRefine((str, ctx) => {
      let parsed: unknown
      try {
        parsed = JSON.parse(str)
      } catch (e) {
        ctx.addIssue({ code: 'custom', message: 'Неверный JSON: ' + (e as Error).message })
        return
      }
      const result = recommendationSchema.safeParse(parsed)
      if (!result.success) {
        const firstErr = result.error.issues[0]
        const msg = firstErr ? `${firstErr.path.join('.') || 'root'}: ${firstErr.message}` : 'Структура рекомендации некорректна'
        ctx.addIssue({ code: 'custom', message: msg })
      }
    }),
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
 * Стартовое значение для нового правила: пустая `all`-группа +
 * минимально-валидный шаблон рекомендации. Для онбординга «как это выглядит».
 */
export const NEW_RULE_DEFAULTS = {
  number: 1,
  group: 'basic_universal' as RuleGroup,
  name: '',
  description: '',
  conditionJson: stringifyJson({ all: [] }),
  recommendationJson: stringifyJson({
    category: 'strategy',
    title: '',
    priority: 'medium',
    reasoning: '',
  }),
  priority: 0,
  is_active: true,
} satisfies RuleFormValues
