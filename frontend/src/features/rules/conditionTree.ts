/**
 * Дерево условия для UI-конструктора. Бэк хранит condition как рекурсивный
 * JSON `{all: [...]} | {any: [...]} | {param, op, value}`. Здесь — типизация
 * под форму + helpers для round-trip JSON ↔ tree.
 *
 * `jsonToTree` возвращает null, если структура слишком экзотична (вложенные
 * операторы lookup_*, странные value) — тогда форма откатится в JSON-режим.
 */
import { getParam, type ConditionOp } from './paramMetadata'

export type ConditionNode = GroupNode | AtomNode

export interface GroupNode {
  kind: 'group'
  /** «Все условия» (and) или «Любое из» (or). */
  combinator: 'all' | 'any'
  children: ConditionNode[]
}

export interface AtomNode {
  kind: 'atom'
  param: string
  op: ConditionOp
  /** Хранится как строка для удобства UI; на сохранении конвертируется по типу param. */
  value: string
}

// ── tree → JSON ─────────────────────────────────────────────────────────────

/**
 * Сериализация дерева в JSON для бэка. Конвертирует value по типу параметра:
 * boolean → true/false, number → число, для in/not_in → массив (split по запятой).
 */
export function treeToJson(node: ConditionNode): Record<string, unknown> {
  if (node.kind === 'group') {
    return { [node.combinator]: node.children.map(treeToJson) }
  }
  return {
    param: node.param,
    op: node.op,
    value: coerceValue(node),
  }
}

function coerceValue(atom: AtomNode): unknown {
  const meta = getParam(atom.param)
  const raw = atom.value

  // Массивы для in / not_in — сплит по запятой
  if (atom.op === 'in' || atom.op === 'not_in') {
    return raw
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean)
      .map((v) => coerceScalar(v, meta?.kind))
  }

  return coerceScalar(raw, meta?.kind)
}

function coerceScalar(raw: string, kind: 'enum' | 'number' | 'boolean' | undefined): unknown {
  if (kind === 'boolean') return raw === 'true'
  if (kind === 'number') {
    const n = Number(raw)
    return Number.isFinite(n) ? n : raw
  }
  return raw
}

// ── JSON → tree ─────────────────────────────────────────────────────────────

/**
 * Парсинг JSON в дерево. Возвращает null, если встретил что-то незнакомое
 * (lookup_*, неизвестный param, неподходящий тип value). UI в этом случае
 * автоматически переключится в JSON-режим — ничего не теряется.
 */
export function jsonToTree(json: unknown): ConditionNode | null {
  if (!isObject(json)) return null

  if ('all' in json && Array.isArray(json.all)) {
    const children = json.all.map(jsonToTree)
    if (children.some((c) => c === null)) return null
    return {
      kind: 'group',
      combinator: 'all',
      children: children as ConditionNode[],
    }
  }

  if ('any' in json && Array.isArray(json.any)) {
    const children = json.any.map(jsonToTree)
    if (children.some((c) => c === null)) return null
    return {
      kind: 'group',
      combinator: 'any',
      children: children as ConditionNode[],
    }
  }

  if ('param' in json && 'op' in json && 'value' in json) {
    const param = String(json.param)
    const op = String(json.op) as ConditionOp
    if (op === 'lookup_eq' || op === 'lookup_neq') return null
    if (!getParam(param)) return null

    return {
      kind: 'atom',
      param,
      op,
      value: stringifyValue(json.value),
    }
  }

  return null
}

function stringifyValue(v: unknown): string {
  if (v === null || v === undefined) return ''
  if (Array.isArray(v)) return v.map(stringifyValue).join(', ')
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}

function isObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

// ── Конструкторы для UI-кнопок ──────────────────────────────────────────────

export function newAtom(): AtomNode {
  return { kind: 'atom', param: 'career_goal', op: 'eq', value: 'ml' }
}

export function newGroup(combinator: 'all' | 'any' = 'all'): GroupNode {
  return { kind: 'group', combinator, children: [newAtom()] }
}

export function newEmptyAllGroup(): GroupNode {
  return { kind: 'group', combinator: 'all', children: [] }
}
