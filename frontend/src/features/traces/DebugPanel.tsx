import { Lightning, Database, Wrench, UserCircle } from '@phosphor-icons/react'
import {
  CAREER_GOAL_LABELS,
  TECHPARK_STATUS_LABELS,
  WORKLOAD_PREF_LABELS,
} from '@/constants/enums'
import type {
  CareerGoal,
  ChatResponse,
  TechparkStatus,
  WorkloadPref,
} from '@/types/api'

interface DebugPanelProps {
  response: ChatResponse | null
  onRuleClick?: (ruleNumber: number) => void
}

/**
 * Правая колонка trace-инспектора. 4 секции на основе debug-ответа LLM:
 *  - rules_fired — какие правила ЭС сработали
 *  - rag_chunks — какие фрагменты вытащил RAG
 *  - tool_calls — какие функции LLM позвала (показываем человеческой строкой,
 *    не сырым `function() + JSON`)
 *  - profile_changes — что LLM решила обновить в профиле (тоже по-русски:
 *    «Цель → ML», а не `{"career_goal": "ml"}`)
 *
 * Если debug=null (LLM не отдала debug-инфу или ещё нет запроса) — empty state.
 */
export function DebugPanel({ response, onRuleClick }: DebugPanelProps) {
  if (!response) {
    return (
      <Empty
        title="Жду запрос"
        description="Слева напиши сообщение от лица студента — здесь появится разбор того, что отработало внутри LLM-оркестратора."
      />
    )
  }

  const debug = response.debug
  if (!debug) {
    return (
      <Empty
        title="Без отладочной информации"
        description="LLM не вернула отладочные данные для этого запроса. Возможно, вызов прошёл без tool-call'ов."
      />
    )
  }

  const rules = debug.rules_fired ?? []
  const ragChunks = debug.rag_chunks ?? []
  const toolCalls = debug.tool_calls ?? []
  const profileChanges = debug.profile_changes ?? {}

  return (
    <div className="flex h-full min-h-0 flex-col gap-[var(--space-lg)] overflow-y-auto px-[var(--space-base)] py-[var(--space-base)]">
      <Section
        icon={<Lightning size={14} weight="regular" />}
        title="Сработавшие правила"
        count={rules.length}
      >
        {rules.length === 0 ? (
          <Hint>ЭС в этом ответе не вызывалась.</Hint>
        ) : (
          <ul className="flex flex-wrap gap-[var(--space-xs)]">
            {rules.map((rid) => {
              const num = parseRuleNumber(rid)
              const clickable = num !== null && Boolean(onRuleClick)
              return (
                <li key={rid}>
                  <button
                    type="button"
                    disabled={!clickable}
                    onClick={() => num !== null && onRuleClick?.(num)}
                    className={
                      'rounded-[6px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[2px] font-mono text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-primary)] transition-colors ' +
                      (clickable
                        ? 'cursor-pointer hover:border-[color:var(--color-border-strong)] hover:bg-[color:var(--color-surface-hover)]'
                        : 'cursor-default')
                    }
                  >
                    {rid}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </Section>

      <Section
        icon={<Database size={14} weight="regular" />}
        title="RAG-фрагменты"
        count={ragChunks.length}
      >
        {ragChunks.length === 0 ? (
          <Hint>RAG-поиск не вызывался.</Hint>
        ) : (
          <ul className="flex flex-col gap-[var(--space-xs)]">
            {ragChunks.map((chunk, i) => (
              <li
                key={i}
                className="rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[var(--space-xs)] font-mono text-[length:var(--text-xs)] break-all text-[color:var(--color-text-muted)]"
              >
                {chunk}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        icon={<Wrench size={14} weight="regular" />}
        title="Действия LLM"
        count={toolCalls.length}
      >
        {toolCalls.length === 0 ? (
          <Hint>LLM ответила без вызова функций.</Hint>
        ) : (
          <ul className="flex flex-col gap-[var(--space-xs)]">
            {toolCalls.map((tc, i) => {
              const { label, details } = describeToolCall(tc)
              return (
                <li
                  key={i}
                  className="flex flex-col gap-[2px] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[var(--space-xs)]"
                >
                  <span className="text-[length:var(--text-sm)] text-[color:var(--color-text)]">
                    {label}
                  </span>
                  {details && (
                    <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
                      {details}
                    </span>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </Section>

      <Section
        icon={<UserCircle size={14} weight="regular" />}
        title="Изменения профиля"
        count={Object.keys(profileChanges).length}
      >
        {Object.keys(profileChanges).length === 0 ? (
          <Hint>LLM не предложила изменений профиля.</Hint>
        ) : (
          <ul className="flex flex-col gap-[var(--space-xs)]">
            {Object.entries(profileChanges).map(([field, value]) => (
              <li
                key={field}
                className="flex items-baseline justify-between gap-[var(--space-sm)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[var(--space-xs)] text-[length:var(--text-sm)]"
              >
                <span className="text-[color:var(--color-text-muted)]">
                  {PROFILE_FIELD_LABELS[field] ?? field}
                </span>
                <span className="font-medium text-[color:var(--color-text)]">
                  {formatProfileValue(field, value)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </Section>
    </div>
  )
}

// ── Section / Hint / Empty ──────────────────────────────────────────────────

interface SectionProps {
  icon: React.ReactNode
  title: string
  count: number
  children: React.ReactNode
}

function Section({ icon, title, count, children }: SectionProps) {
  return (
    <section className="flex flex-col gap-[var(--space-sm)]">
      <header className="flex items-center justify-between gap-[var(--space-sm)]">
        <span className="flex items-center gap-[var(--space-xs)] font-serif text-[length:var(--text-sm)] font-semibold tracking-tight text-[color:var(--color-text)]">
          <span className="text-[color:var(--color-text-muted)]">{icon}</span>
          {title}
        </span>
        <span className="text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-subtle)]">
          {count}
        </span>
      </header>
      {children}
    </section>
  )
}

function Hint({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
      {children}
    </p>
  )
}

function Empty({ title, description }: { title: string; description: string }) {
  return (
    <div className="flex h-full items-center justify-center px-[var(--space-2xl)]">
      <div className="flex max-w-[40ch] flex-col gap-[var(--space-sm)] text-center">
        <h3 className="font-serif text-[length:var(--text-md)] font-semibold tracking-tight text-[color:var(--color-text)]">
          {title}
        </h3>
        <p className="text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text-muted)]">
          {description}
        </p>
      </div>
    </div>
  )
}

// ── Перевод tool-calls и profile_changes в человеческий вид ─────────────────

type ToolCall = { function: string; arguments: Record<string, unknown> }

/** Лейблы полей профиля для секции «Изменения профиля» и расшифровки changes. */
const PROFILE_FIELD_LABELS: Record<string, string> = {
  career_goal: 'Цель',
  technopark_status: 'Технопарк',
  workload_pref: 'Нагрузка',
  semester: 'Семестр',
}

/**
 * Переводит tool-call в человеческую строку. Знает три функции из CLAUDE.md
 * (get_recommendations / recalculate_with_changes / search_knowledge);
 * незнакомые функции отрендерит как `function_name` + сырые args, чтобы
 * новые tool-call'ы не исчезали молча.
 */
function describeToolCall(tc: ToolCall): { label: string; details?: string } {
  const args = tc.arguments ?? {}
  switch (tc.function) {
    case 'get_recommendations':
      return { label: 'Запрошены текущие рекомендации' }

    case 'recalculate_with_changes': {
      const changes = (args.changes ?? args) as Record<string, unknown>
      const details = formatChanges(changes)
      return details
        ? { label: 'Пересчёт с изменениями', details }
        : { label: 'Пересчёт с изменениями' }
    }

    case 'search_knowledge': {
      const query = String(args.query ?? '').trim()
      return query
        ? { label: 'Поиск в базе знаний', details: `«${query}»` }
        : { label: 'Поиск в базе знаний' }
    }

    default:
      return Object.keys(args).length > 0
        ? { label: tc.function, details: JSON.stringify(args) }
        : { label: tc.function }
  }
}

/** Список изменений профиля в одну строку: «Цель → ML; Нагрузка → лёгкая». */
function formatChanges(changes: Record<string, unknown>): string {
  return Object.entries(changes)
    .map(([key, val]) => {
      const label = PROFILE_FIELD_LABELS[key] ?? key
      return `${label} → ${formatProfileValue(key, val)}`
    })
    .join('; ')
}

/** Значение поля профиля в человеческом виде (использует существующие лейблы enum'ов). */
function formatProfileValue(field: string, val: unknown): string {
  if (val === null || val === undefined) return '—'
  if (field === 'career_goal' && typeof val === 'string') {
    return CAREER_GOAL_LABELS[val as CareerGoal] ?? val
  }
  if (field === 'technopark_status' && typeof val === 'string') {
    return TECHPARK_STATUS_LABELS[val as TechparkStatus] ?? val
  }
  if (field === 'workload_pref' && typeof val === 'string') {
    return WORKLOAD_PREF_LABELS[val as WorkloadPref] ?? val
  }
  if (typeof val === 'object') return JSON.stringify(val)
  return String(val)
}

function parseRuleNumber(rid: string): number | null {
  const m = rid.match(/(\d+)/)
  return m ? Number(m[1]) : null
}
