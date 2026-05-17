import { Plus, X, Stack } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'
import { pluralize } from '@/lib/plural'
import {
  getGroupedParams,
  getParam,
  OP_LABELS,
  PARAMS,
  type ConditionOp,
} from './paramMetadata'
import {
  newAtom,
  newGroup,
  type AtomNode,
  type ConditionNode,
  type GroupNode,
} from './conditionTree'

interface ConditionBuilderProps {
  value: GroupNode
  onChange: (next: GroupNode) => void
  disabled?: boolean
}

/**
 * Визуальный конструктор условия. Заменяет сырое JSON для большинства правил
 * (lookup_* и вложенные кейсы — через mode toggle на JSON в RuleForm).
 *
 * Корень — всегда group. Внутри — атомы или вложенные группы. Глубина не
 * ограничена, но визуально подойдёт 2 уровня.
 */
export function ConditionBuilder({ value, onChange, disabled = false }: ConditionBuilderProps) {
  return (
    <GroupView
      node={value}
      onChange={onChange}
      onDelete={null}
      disabled={disabled}
      depth={0}
    />
  )
}

// ── Группа (all / any) ──────────────────────────────────────────────────────

interface GroupViewProps {
  node: GroupNode
  onChange: (next: GroupNode) => void
  /** null для root-группы (её нельзя удалить). */
  onDelete: (() => void) | null
  disabled: boolean
  depth: number
}

function GroupView({ node, onChange, onDelete, disabled, depth }: GroupViewProps) {
  const updateChild = (i: number, next: ConditionNode) => {
    const children = node.children.slice()
    children[i] = next
    onChange({ ...node, children })
  }

  const removeChild = (i: number) => {
    onChange({ ...node, children: node.children.filter((_, j) => j !== i) })
  }

  const addAtom = () => {
    onChange({ ...node, children: [...node.children, newAtom()] })
  }

  const addGroup = () => {
    onChange({ ...node, children: [...node.children, newGroup('all')] })
  }

  return (
    <div
      className={cn(
        'flex flex-col gap-[var(--space-sm)] rounded-[8px] border bg-[color:var(--color-surface-muted)] p-[var(--space-sm)]',
        depth === 0
          ? 'border-[color:var(--color-border)]'
          : 'border-[color:var(--color-border)]',
      )}
    >
      {/* Header: combinator + delete (если не root) */}
      <header className="flex items-center gap-[var(--space-sm)]">
        <Select
          value={node.combinator}
          onValueChange={(v) =>
            onChange({ ...node, combinator: v as 'all' | 'any' })
          }
          disabled={disabled}
        >
          <SelectTrigger size="sm" className="w-[180px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Все условия (И)</SelectItem>
            <SelectItem value="any">Любое из (ИЛИ)</SelectItem>
          </SelectContent>
        </Select>

        <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
          {node.children.length === 0
            ? 'пустая группа'
            : `${node.children.length} ${pluralize(node.children.length, 'элемент', 'элемента', 'элементов')}`}
        </span>

        {onDelete && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={onDelete}
                disabled={disabled}
                aria-label="Удалить группу"
                className="ml-auto"
              >
                <X size={14} />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Удалить группу со всеми вложенными</TooltipContent>
          </Tooltip>
        )}
      </header>

      {/* Children */}
      {node.children.length > 0 && (
        <div className="flex flex-col gap-[var(--space-sm)]">
          {node.children.map((child, i) => (
            <div key={i}>
              {child.kind === 'atom' ? (
                <AtomView
                  node={child}
                  onChange={(next) => updateChild(i, next)}
                  onDelete={() => removeChild(i)}
                  disabled={disabled}
                />
              ) : (
                <GroupView
                  node={child}
                  onChange={(next) => updateChild(i, next)}
                  onDelete={() => removeChild(i)}
                  disabled={disabled}
                  depth={depth + 1}
                />
              )}
            </div>
          ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-[var(--space-xs)]">
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={addAtom}
          disabled={disabled}
        >
          <Plus size={12} weight="bold" />
          Условие
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={addGroup}
          disabled={disabled}
        >
          <Stack size={12} weight="regular" />
          Вложенная группа
        </Button>
      </div>
    </div>
  )
}

// ── Атом (param + op + value) ───────────────────────────────────────────────

interface AtomViewProps {
  node: AtomNode
  onChange: (next: AtomNode) => void
  onDelete: () => void
  disabled: boolean
}

function AtomView({ node, onChange, onDelete, disabled }: AtomViewProps) {
  const meta = getParam(node.param)
  const grouped = getGroupedParams()

  const handleParamChange = (newParam: string) => {
    const newMeta = getParam(newParam)
    if (!newMeta) return
    // Если текущий оператор не поддерживается новым параметром — берём первый.
    const op = newMeta.ops.includes(node.op) ? node.op : newMeta.ops[0]!
    // Значение тоже сбрасываем — оно может быть невалидным для нового типа.
    const value = defaultValueFor(newMeta)
    onChange({ kind: 'atom', param: newParam, op, value })
  }

  const handleOpChange = (newOp: string) => {
    const op = newOp as ConditionOp
    // При переходе в/из in/not_in значение нужно адаптировать.
    const wasMulti = node.op === 'in' || node.op === 'not_in'
    const isMulti = op === 'in' || op === 'not_in'
    let value = node.value
    if (wasMulti !== isMulti) {
      value = wasMulti ? value.split(',')[0]?.trim() ?? '' : value
    }
    onChange({ ...node, op, value })
  }

  return (
    <div className="flex flex-wrap items-center gap-[var(--space-xs)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-xs)]">
      {/* Параметр */}
      <Select value={node.param} onValueChange={handleParamChange} disabled={disabled}>
        <SelectTrigger size="sm" className="w-[220px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent className="max-h-[320px]">
          {grouped.map(({ group, label, items }) => (
            <div key={group}>
              <div className="px-[var(--space-sm)] pt-[var(--space-sm)] pb-[var(--space-xs)] text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
                {label}
              </div>
              {items.map((p) => (
                <SelectItem key={p.name} value={p.name}>
                  {p.label}
                </SelectItem>
              ))}
            </div>
          ))}
        </SelectContent>
      </Select>

      {/* Оператор */}
      <Select
        value={node.op}
        onValueChange={handleOpChange}
        disabled={disabled || !meta}
      >
        <SelectTrigger size="sm" className="w-[180px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {(meta?.ops ?? PARAMS[0]!.ops).map((op) => (
            <SelectItem key={op} value={op}>
              {OP_LABELS[op]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* Значение */}
      <div className="min-w-[200px] flex-1">
        <ValueControl
          meta={meta}
          op={node.op}
          value={node.value}
          onChange={(v) => onChange({ ...node, value: v })}
          disabled={disabled}
        />
      </div>

      {/* Удалить */}
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={onDelete}
            disabled={disabled}
            aria-label="Удалить условие"
          >
            <X size={14} />
          </Button>
        </TooltipTrigger>
        <TooltipContent>Удалить условие</TooltipContent>
      </Tooltip>
    </div>
  )
}

// ── Значение (контрол под тип) ──────────────────────────────────────────────

interface ValueControlProps {
  meta: ReturnType<typeof getParam>
  op: ConditionOp
  value: string
  onChange: (v: string) => void
  disabled: boolean
}

function ValueControl({ meta, op, value, onChange, disabled }: ValueControlProps) {
  if (!meta) {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="значение"
      />
    )
  }

  const isMulti = op === 'in' || op === 'not_in'

  // in / not_in — даже для enum показываем Input с подсказкой «через запятую»
  if (isMulti) {
    return (
      <Input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        placeholder="значения через запятую"
      />
    )
  }

  if (meta.kind === 'boolean' || meta.kind === 'enum') {
    return (
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger size="sm" className="w-full">
          <SelectValue placeholder="Выбрать…" />
        </SelectTrigger>
        <SelectContent>
          {(meta.values ?? []).map((v) => (
            <SelectItem key={v.value} value={v.value}>
              {v.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  }

  // number
  return (
    <Input
      type="number"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      min={meta.min}
      max={meta.max}
      placeholder="число"
    />
  )
}

// ── Утилиты ─────────────────────────────────────────────────────────────────

function defaultValueFor(meta: ReturnType<typeof getParam>): string {
  if (!meta) return ''
  if (meta.kind === 'boolean') return 'true'
  if (meta.kind === 'enum') return meta.values?.[0]?.value ?? ''
  if (meta.kind === 'number') return String(meta.min ?? 0)
  return ''
}

