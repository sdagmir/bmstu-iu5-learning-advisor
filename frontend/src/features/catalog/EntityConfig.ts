import type { ReactNode } from 'react'
import type { ZodType } from 'zod'

/**
 * Тип поля формы. От него зависит, как `CrudForm` отрендерит контрол.
 */
export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'select'
  | 'multiselect'
  | 'switch'

export interface SelectOption {
  value: string
  label: string
}

/** Описание поля формы (общее для create и edit). */
export interface FieldConfig<TForm> {
  name: keyof TForm & string
  label: string
  type: FieldType
  /** Для select/multiselect — список или функция, возвращающая список (для динамических). */
  options?: SelectOption[] | (() => SelectOption[] | Promise<SelectOption[]>)
  placeholder?: string
  hint?: string
  /** В каких режимах показывать поле. По умолчанию — везде. */
  showIn?: ReadonlyArray<'create' | 'edit'>
  /** Делает поле read-only в edit (например, email пользователя). */
  readOnlyOnEdit?: boolean
}

/** Описание колонки таблицы. */
export interface ColumnConfig<TRead> {
  key: keyof TRead & string
  label: string
  /** Кастомный рендер: например, чип категории с цветом. */
  render?: (row: TRead) => ReactNode
  /** Жёсткая ширина (px). Без неё колонка `1fr`. */
  width?: number
  /** Моноспейс tabular-nums для tag/credits/semester. */
  mono?: boolean
}

/**
 * Полная конфигурация одной сущности каталога.
 * `TRead` — тип элемента из списка/детали; `TForm` — что вводится в форме
 * (обычно совпадает с *Create-схемой бэка).
 *
 * Если `create`/`delete` отсутствуют — у пользователя не появляется кнопка
 * (например, у `users` нельзя создавать или удалять — только править роль).
 */
export interface EntityConfig<TRead extends { id: string }, TForm> {
  key: string
  /** Заголовок в шапке страницы и в текстах диалогов («Создать **компетенцию**»). */
  singular: string
  pluralName: string
  list: () => Promise<TRead[]>
  create?: (body: TForm) => Promise<TRead>
  update?: (id: string, body: Partial<TForm>) => Promise<TRead>
  delete?: (id: string) => Promise<void>
  columns: Array<ColumnConfig<TRead>>
  fields: Array<FieldConfig<TForm>>
  /** Zod-схема для валидации формы (общая для create/edit). */
  schema: ZodType<TForm>
  /** Как из `TRead` сделать значения для редактирования. */
  toFormValues: (row: TRead) => TForm
  /** Дефолтные значения для create. */
  emptyFormValues: () => TForm
  /** Уникальный ключ строки в текстах подтверждений (`Удалить «{name}»?`). */
  rowLabel: (row: TRead) => string
}
