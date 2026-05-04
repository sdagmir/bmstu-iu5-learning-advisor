import { useEffect, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useDebouncedValue } from '@/hooks/useDebouncedValue'
import { usePersistentState } from '@/hooks/usePersistentState'
import { simulatorApi } from './api'
import type { EvaluateDebugResponse, SimulatorProfile } from '@/types/api'

const DEBOUNCE_MS = 250

/**
 * Управляет state профиля симулятора + debounced запуск /expert/evaluate/debug.
 * При каждом «спокойном» изменении профиля (250ms без правок) — пересчёт.
 *
 * Profile persist'ится в `sessionStorage` — настроенные X1-X12 переживают
 * навигацию по другим экранам админки. Result не persist'им: его дешевле
 * пересчитать на mount (debounced effect отстреливает сам).
 */
export function useSimulator(initial: SimulatorProfile) {
  const [profile, setProfile] = usePersistentState<SimulatorProfile>(
    'admin.simulator.profile',
    initial,
  )
  const [result, setResult] = useState<EvaluateDebugResponse | null>(null)
  const debouncedProfile = useDebouncedValue(profile, DEBOUNCE_MS)

  const mut = useMutation({
    mutationFn: (p: SimulatorProfile) => simulatorApi.evaluateDebug(p),
    onSuccess: (data) => setResult(data),
  })

  const { mutate } = mut

  useEffect(() => {
    mutate(debouncedProfile)
  }, [debouncedProfile, mutate])

  /** Точечно обновить одно поле (или несколько). */
  const update = (patch: Partial<SimulatorProfile>) => {
    setProfile((p) => ({ ...p, ...patch }))
  }

  /** Заменить весь профиль (используется пресетами). */
  const replace = (next: SimulatorProfile) => {
    setProfile(next)
  }

  return {
    profile,
    update,
    replace,
    result,
    isPending: mut.isPending,
    isError: mut.isError,
  }
}
