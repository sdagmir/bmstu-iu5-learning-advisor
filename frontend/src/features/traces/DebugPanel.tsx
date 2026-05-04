import { Lightning, Database, Wrench, UserCircle } from '@phosphor-icons/react'
import type { ChatResponse } from '@/types/api'

interface DebugPanelProps {
  response: ChatResponse | null
  onRuleClick?: (ruleNumber: number) => void
}

/**
 * Правая колонка trace-инспектора. 4 секции на основе debug-ответа LLM:
 *  - rules_fired — какие правила ЭС сработали
 *  - rag_chunks — какие фрагменты вытащил RAG
 *  - tool_calls — какие функции LLM позвала и с какими аргументами
 *  - profile_changes — что LLM решила обновить в профиле студента
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
        title="Без debug-инфы"
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
          <ul className="flex flex-col gap-[var(--space-xs)]">
            {rules.map((rid) => {
              const num = parseRuleNumber(rid)
              return (
                <li key={rid}>
                  <button
                    type="button"
                    disabled={num === null || !onRuleClick}
                    onClick={() => num !== null && onRuleClick?.(num)}
                    className={
                      'w-full rounded-[6px] px-[var(--space-sm)] py-[var(--space-xs)] text-left transition-colors ' +
                      (num !== null && onRuleClick
                        ? 'hover:bg-[color:var(--color-surface-hover)]'
                        : 'cursor-default')
                    }
                  >
                    <span className="font-mono text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-primary)]">
                      {rid}
                    </span>
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
                className="rounded-[6px] bg-[color:var(--color-surface)] px-[var(--space-sm)] py-[var(--space-xs)] font-mono text-[length:var(--text-xs)] break-all text-[color:var(--color-text-muted)]"
              >
                {chunk}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section
        icon={<Wrench size={14} weight="regular" />}
        title="Tool-call'ы LLM"
        count={toolCalls.length}
      >
        {toolCalls.length === 0 ? (
          <Hint>LLM ответила без вызова функций.</Hint>
        ) : (
          <ul className="flex flex-col gap-[var(--space-sm)]">
            {toolCalls.map((tc, i) => (
              <li
                key={i}
                className="flex flex-col gap-[var(--space-xs)] rounded-[6px] bg-[color:var(--color-surface)] p-[var(--space-sm)]"
              >
                <span className="font-mono text-[length:var(--text-xs)] text-[color:var(--color-primary)]">
                  {tc.function}()
                </span>
                <pre className="overflow-x-auto rounded-[4px] bg-[color:var(--color-surface-muted)] p-[var(--space-xs)] font-mono text-[length:var(--text-xs)] leading-relaxed text-[color:var(--color-text-muted)]">
                  {JSON.stringify(tc.arguments, null, 2)}
                </pre>
              </li>
            ))}
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
          <pre className="overflow-x-auto rounded-[6px] bg-[color:var(--color-surface)] p-[var(--space-sm)] font-mono text-[length:var(--text-xs)] leading-relaxed text-[color:var(--color-text)]">
            {JSON.stringify(profileChanges, null, 2)}
          </pre>
        )}
      </Section>
    </div>
  )
}

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
        <span className="flex items-center gap-[var(--space-xs)] text-[length:var(--text-xs)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          {icon}
          {title}
        </span>
        <span className="text-[length:var(--text-xs)] tabular-nums text-[color:var(--color-text-muted)]">
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
        <span className="text-[length:var(--text-sm)] tracking-wider text-[color:var(--color-text-subtle)] uppercase">
          {title}
        </span>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          {description}
        </p>
      </div>
    </div>
  )
}

function parseRuleNumber(rid: string): number | null {
  const m = rid.match(/(\d+)/)
  return m ? Number(m[1]) : null
}
