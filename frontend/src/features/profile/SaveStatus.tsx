import { useEffect, useState } from 'react'
import { useIsMutating, useQueryClient } from '@tanstack/react-query'
import { CircleNotch, Check } from '@phosphor-icons/react'

const TIME_FORMAT = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

/**
 * Универсальный индикатор сохранения для профиля. Подписывается на mutation
 * cache и считает PROFILE-мутации (по ключу `['profile', ...]`):
 *
 * - patchMe (X1–X4)            → ['profile', 'me']
 * - putGrades                   → ['profile', 'grades']
 * - addCompletedCK / remove     → ['profile', 'completed-ck', ...]
 *
 * Анти-flicker: layout стабильный — лейбл «Сохранено в HH:MM» НЕ переключается
 * на «Сохраняем…» когда идёт следующий save. Меняется только иконка
 * (check ↔ spinner). До первого save показываем «Сохраняем…», дальше всегда
 * timestamp с морфингом иконки. tabular-nums держит ширину времени стабильной.
 */
export function SaveStatus() {
  const queryClient = useQueryClient()
  const pendingCount = useIsMutating({
    predicate: (m) => m.options.mutationKey?.[0] === 'profile',
  })
  const [lastSavedAt, setLastSavedAt] = useState<Date | null>(null)

  useEffect(() => {
    return queryClient.getMutationCache().subscribe((event) => {
      if (event.type !== 'updated' || event.action?.type !== 'success') return
      if (event.mutation.options.mutationKey?.[0] !== 'profile') return
      setLastSavedAt(new Date())
    })
  }, [queryClient])

  const isPending = pendingCount > 0

  // До первого save — простое pending. После — стабильный timestamp с морфингом иконки.
  if (lastSavedAt === null) {
    if (!isPending) return null
    return (
      <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        <CircleNotch size={14} weight="regular" className="animate-spin" />
        Сохраняем…
      </span>
    )
  }

  return (
    <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] tabular-nums text-[color:var(--color-text-muted)]">
      {isPending ? (
        <CircleNotch
          size={14}
          weight="regular"
          className="animate-spin text-[color:var(--color-text-muted)]"
        />
      ) : (
        <Check size={14} weight="bold" className="text-[color:var(--color-success)]" />
      )}
      Сохранено в {TIME_FORMAT.format(lastSavedAt)}
    </span>
  )
}
