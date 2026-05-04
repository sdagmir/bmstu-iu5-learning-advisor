import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ListMagnifyingGlass } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { DebugChat } from '@/features/traces/DebugChat'
import { DebugPanel } from '@/features/traces/DebugPanel'
import { useDebugChat } from '@/features/traces/useDebugChat'
import { rulesApi } from '@/features/rules/api'
import { routes } from '@/constants/routes'

/**
 * Phase 10 — debug-чат как trace-инспектор. На бэке нет полноценного журнала
 * трейсов, зато есть `POST /chat/message/debug` который для каждого запроса
 * возвращает rules_fired / rag_chunks / tool_calls / profile_changes.
 *
 * 2-кол layout: [чат 1fr] [debug-панель 480px]. State `useDebugChat` живёт
 * на странице, чтобы DebugChat и DebugPanel читали один и тот же lastResponse.
 */
export default function TracesPage() {
  const navigate = useNavigate()
  const { history, lastResponse, isPending, send, reset } = useDebugChat()
  const rules = useQuery({
    queryKey: ['admin', 'rules'],
    queryFn: rulesApi.list,
    staleTime: 60_000,
  })

  const onRuleClick = (ruleNumber: number) => {
    const rule = rules.data?.find((r) => r.number === ruleNumber)
    if (!rule) return
    navigate(`${routes.admin.rules}?ruleId=${rule.id}`)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <PageTopBar
        title="Debug-чат LLM"
        icon={<ListMagnifyingGlass size={18} weight="regular" />}
      />
      <div className="grid min-h-0 flex-1 grid-cols-[minmax(0,1fr)_480px] overflow-hidden">
        <main className="min-h-0 overflow-hidden border-r border-[color:var(--color-border)]">
          <DebugChat
            history={history}
            isPending={isPending}
            onSend={send}
            onReset={reset}
          />
        </main>
        <aside className="min-h-0 overflow-hidden bg-[color:var(--color-surface-muted)]">
          <DebugPanel response={lastResponse} onRuleClick={onRuleClick} />
        </aside>
      </div>
    </div>
  )
}
