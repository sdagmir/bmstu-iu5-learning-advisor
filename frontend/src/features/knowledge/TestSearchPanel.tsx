import { useState } from 'react'
import { CircleNotch, MagnifyingGlass } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useRagSearch } from './useKnowledge'

/**
 * Тест-поиск по RAG. Полезно для отладки: ввёл запрос — увидел, какие
 * чанки отдаст бэк с какими score'ами. Используем для калибровки
 * top_k и для проверки, что после загрузки документ ищется.
 */
export function TestSearchPanel() {
  const [query, setQuery] = useState('')
  const search = useRagSearch()

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return
    search.mutate({ query: query.trim(), top_k: 5 })
  }

  const results = search.data ?? []

  return (
    <section className="flex flex-col gap-[var(--space-base)]">
      <header className="flex flex-col gap-[var(--space-xs)]">
        <h2 className="text-[length:var(--text-md)] font-semibold text-[color:var(--color-text)]">
          Тест-поиск
        </h2>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Введи запрос — увидишь топ-5 фрагментов из базы знаний с score'ами.
          Это полная имитация того, что использует LLM при tool-call'е RAG.
        </p>
      </header>

      <form onSubmit={submit} className="flex gap-[var(--space-sm)]">
        <div className="relative flex-1">
          <MagnifyingGlass
            size={14}
            className="pointer-events-none absolute top-1/2 left-[var(--space-sm)] -translate-y-1/2 text-[color:var(--color-text-subtle)]"
          />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="как выбрать ЦК для ML?"
            className="pl-[calc(var(--space-sm)+1.25rem)]"
          />
        </div>
        <Button type="submit" disabled={search.isPending || !query.trim()}>
          {search.isPending ? <CircleNotch size={14} className="animate-spin" /> : null}
          Найти
        </Button>
      </form>

      {search.isSuccess &&
        (results.length === 0 ? (
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
            Ничего не найдено по запросу «{query}».
          </p>
        ) : (
          <ul className="flex flex-col gap-[var(--space-sm)]">
            {results.map((chunk, i) => (
              <li
                key={`${chunk.source}-${i}`}
                className="flex flex-col gap-[var(--space-xs)] rounded-[8px] border border-[color:var(--color-border)] bg-[color:var(--color-surface)] p-[var(--space-base)]"
              >
                <div className="flex items-center justify-between gap-[var(--space-sm)] text-[length:var(--text-xs)]">
                  <span className="font-mono text-[color:var(--color-text-muted)]">
                    {chunk.source}
                  </span>
                  <span className="tabular-nums text-[color:var(--color-text-subtle)]">
                    score {chunk.score.toFixed(3)}
                  </span>
                </div>
                <p className="text-[length:var(--text-sm)] leading-relaxed text-[color:var(--color-text)]">
                  {chunk.content}
                </p>
              </li>
            ))}
          </ul>
        ))}
    </section>
  )
}
