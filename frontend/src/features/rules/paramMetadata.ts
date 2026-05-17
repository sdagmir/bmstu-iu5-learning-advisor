/**
 * Метаданные параметров X1–X12 для конструктора условия.
 * Источники: `backend/app/expert/schemas.py` (StudentProfile + StrEnum'ы) и
 * `frontend/src/constants/enums.ts` (русские лейблы целей/треков/нагрузки).
 *
 * Захардкожено намеренно: бэк не отдаёт schema-эндпоинт, а правила правят
 * редко — синхронизация раз в полгода через ревью PR.
 */
import {
  ALL_CAREER_GOALS,
  ALL_TECHPARK_STATUSES,
  ALL_WORKLOAD_PREFS,
  CAREER_GOAL_LABELS,
  TECHPARK_STATUS_LABELS,
  WORKLOAD_PREF_LABELS,
} from '@/constants/enums'

/** Все операторы, которые принимает бэк. lookup_* — экзотика, не в builder. */
export type ConditionOp =
  | 'eq'
  | 'neq'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'in'
  | 'not_in'
  | 'lookup_eq'
  | 'lookup_neq'

export const OP_LABELS: Record<ConditionOp, string> = {
  eq: 'равно',
  neq: 'не равно',
  gt: 'больше',
  gte: 'больше или равно',
  lt: 'меньше',
  lte: 'меньше или равно',
  in: 'в наборе',
  not_in: 'не в наборе',
  lookup_eq: 'lookup =',
  lookup_neq: 'lookup ≠',
}

/** Опция значения для enum-параметра — машинный тег + человеческий лейбл. */
export interface ValueOption {
  value: string
  label: string
}

type ParamKind = 'enum' | 'number' | 'boolean'

export interface ParamMetadata {
  name: string
  label: string
  /** Группа в Select — помогает сгруппировать визуально (профиль / прогресс / слабые места). */
  group: 'profile' | 'progress' | 'gaps' | 'derived'
  kind: ParamKind
  /** Операторы, имеющие смысл для этого типа значения. */
  ops: ConditionOp[]
  /** Для enum — список допустимых значений с лейблами. */
  values?: ValueOption[]
  /** Для number — границы (для подсказки в Input). */
  min?: number
  max?: number
}

const BOOL_OPS: ConditionOp[] = ['eq']
const NUMBER_OPS: ConditionOp[] = ['eq', 'neq', 'gt', 'gte', 'lt', 'lte']
const ENUM_OPS: ConditionOp[] = ['eq', 'neq', 'in', 'not_in']

/** Универсальный значения для bool — два лейбла. */
export const BOOL_VALUES: ValueOption[] = [
  { value: 'true', label: 'Да' },
  { value: 'false', label: 'Нет' },
]

function toValueOptions<T extends string>(
  values: readonly T[],
  labels: Record<T, string>,
): ValueOption[] {
  return values.map((v) => ({ value: v, label: labels[v] }))
}

/** Метаданные всех 12 параметров. */
export const PARAMS: ParamMetadata[] = [
  // ── Профиль студента ─────────────────────────────────────────────────
  {
    name: 'career_goal',
    label: 'Карьерная цель',
    group: 'profile',
    kind: 'enum',
    ops: ENUM_OPS,
    values: toValueOptions(ALL_CAREER_GOALS, CAREER_GOAL_LABELS),
  },
  {
    name: 'semester',
    label: 'Семестр',
    group: 'profile',
    kind: 'number',
    ops: NUMBER_OPS,
    min: 1,
    max: 8,
  },
  {
    name: 'technopark_status',
    label: 'Технопарк',
    group: 'profile',
    kind: 'enum',
    ops: ENUM_OPS,
    values: toValueOptions(ALL_TECHPARK_STATUSES, TECHPARK_STATUS_LABELS),
  },
  {
    name: 'workload_pref',
    label: 'Нагрузка',
    group: 'profile',
    kind: 'enum',
    ops: ENUM_OPS,
    values: toValueOptions(ALL_WORKLOAD_PREFS, WORKLOAD_PREF_LABELS),
  },

  // ── Прогресс по ЦК (X5–X8) ───────────────────────────────────────────
  {
    name: 'completed_ck_ml',
    label: 'Прошёл ЦК по ML',
    group: 'progress',
    kind: 'boolean',
    ops: BOOL_OPS,
    values: BOOL_VALUES,
  },
  {
    name: 'ck_dev_status',
    label: 'Статус ЦК по разработке',
    group: 'progress',
    kind: 'enum',
    ops: ENUM_OPS,
    values: [
      { value: 'yes', label: 'Пройден' },
      { value: 'partial', label: 'Частично' },
      { value: 'no', label: 'Не проходил' },
    ],
  },
  {
    name: 'completed_ck_security',
    label: 'Прошёл ЦК по безопасности',
    group: 'progress',
    kind: 'boolean',
    ops: BOOL_OPS,
    values: BOOL_VALUES,
  },
  {
    name: 'completed_ck_testing',
    label: 'Прошёл ЦК по тестированию',
    group: 'progress',
    kind: 'boolean',
    ops: BOOL_OPS,
    values: BOOL_VALUES,
  },

  // ── Слабые места (X9–X10) ────────────────────────────────────────────
  {
    name: 'weak_math',
    label: 'Слабая база по математике',
    group: 'gaps',
    kind: 'boolean',
    ops: BOOL_OPS,
    values: BOOL_VALUES,
  },
  {
    name: 'weak_programming',
    label: 'Слабая база по программированию',
    group: 'gaps',
    kind: 'boolean',
    ops: BOOL_OPS,
    values: BOOL_VALUES,
  },

  // ── Производные показатели (X11–X12) ─────────────────────────────────
  {
    name: 'coverage',
    label: 'Покрытие профиля',
    group: 'derived',
    kind: 'enum',
    ops: ENUM_OPS,
    values: [
      { value: 'low', label: 'Низкое (< 30%)' },
      { value: 'medium', label: 'Среднее (30–70%)' },
      { value: 'high', label: 'Высокое (> 70%)' },
    ],
  },
  {
    name: 'ck_count_in_category',
    label: 'Курсов ЦК в одной категории',
    group: 'derived',
    kind: 'enum',
    ops: ENUM_OPS,
    values: [
      { value: 'few', label: '0–2 курса' },
      { value: 'many', label: '3+ курса' },
    ],
  },
]

export const PARAM_GROUP_LABELS: Record<ParamMetadata['group'], string> = {
  profile: 'Профиль студента',
  progress: 'Прогресс по ЦК',
  gaps: 'Слабые базы',
  derived: 'Производные',
}

/** Быстрый lookup по имени параметра. */
const PARAM_BY_NAME = new Map(PARAMS.map((p) => [p.name, p]))

export function getParam(name: string): ParamMetadata | undefined {
  return PARAM_BY_NAME.get(name)
}

/** Группировка параметров для рендера в Select. */
export function getGroupedParams(): Array<{
  group: ParamMetadata['group']
  label: string
  items: ParamMetadata[]
}> {
  const groups: ParamMetadata['group'][] = ['profile', 'progress', 'gaps', 'derived']
  return groups.map((g) => ({
    group: g,
    label: PARAM_GROUP_LABELS[g],
    items: PARAMS.filter((p) => p.group === g),
  }))
}
