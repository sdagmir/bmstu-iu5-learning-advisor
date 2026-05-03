import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { rulesApi } from './api'
import { useRuleLockStore } from '@/stores/ruleLockStore'
import { useAuthStore } from '@/stores/authStore'

const LOCK_QUERY_KEY = ['admin', 'rules', 'lock'] as const
/** Порог автопродления — лок продлевается когда осталось меньше этого. */
const RENEW_THRESHOLD_S = 5 * 60
/** Период повторных попыток продления. */
const RENEW_RETRY_S = 30
/** Период тика секундомера. */
const TICK_MS = 1000

/**
 * Единая точка интеграции с lock-конструктором. Делает следующее:
 *  - GET /admin/rules/lock на mount → setStatus
 *  - Раз в секунду пересчитывает `secondsLeft` из `expires_at`
 *  - Когда лок мой и осталось < 5 минут — фоновый POST /lock (продление)
 *  - Слушает `rule-lock-lost` (диспатчится из api-client на 423) →
 *    переводит owned_by_me в false и показывает toast «Лок утрачен».
 *  - На unmount / beforeunload — DELETE /lock через keepalive fetch
 *
 * Возвращает: status, secondsLeft, флаги, мутации acquire/release/forceRelease,
 * а также производное `canEdit` для гейта на mutating-кнопках.
 */
export function useRuleLock() {
  const queryClient = useQueryClient()
  const status = useRuleLockStore((s) => s.status)
  const setStatus = useRuleLockStore((s) => s.setStatus)

  // Грузим статус один раз; обновляем кэш store вручную из onSuccess мутаций.
  const statusQuery = useQuery({
    queryKey: LOCK_QUERY_KEY,
    queryFn: rulesApi.lock.status,
    staleTime: 60_000,
  })

  useEffect(() => {
    if (statusQuery.data) setStatus(statusQuery.data)
  }, [statusQuery.data, setStatus])

  const acquireMut = useMutation({
    mutationKey: ['admin', 'rules', 'lock', 'acquire'],
    mutationFn: rulesApi.lock.acquire,
    onSuccess: (data) => {
      setStatus(data)
      queryClient.setQueryData(LOCK_QUERY_KEY, data)
    },
    onError: () => {
      toast.error('Не удалось войти в редактор. Возможно, кто-то опередил.')
      void queryClient.invalidateQueries({ queryKey: LOCK_QUERY_KEY })
    },
  })

  const releaseMut = useMutation({
    mutationKey: ['admin', 'rules', 'lock', 'release'],
    mutationFn: rulesApi.lock.release,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: LOCK_QUERY_KEY })
    },
  })

  const forceReleaseMut = useMutation({
    mutationKey: ['admin', 'rules', 'lock', 'force-release'],
    mutationFn: rulesApi.lock.forceRelease,
    onSuccess: () => {
      toast.success('Лок освобождён. Можно входить в редактор.')
      void queryClient.invalidateQueries({ queryKey: LOCK_QUERY_KEY })
    },
    onError: () => {
      toast.error('Не удалось освободить лок')
    },
  })

  // ── Тик 1Гц для пересчёта secondsLeft из expires_at ─────────────────────
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!status?.owned_by_me || !status.expires_at) return
    const id = window.setInterval(() => setNow(Date.now()), TICK_MS)
    return () => window.clearInterval(id)
  }, [status?.owned_by_me, status?.expires_at])

  const secondsLeft: number | null = status?.expires_at
    ? Math.max(0, Math.floor((new Date(status.expires_at).getTime() - now) / 1000))
    : null

  // ── Автопродление: <5 мин до истечения, не чаще раза в 30 сек ───────────
  const lastRenewAt = useRef(0)
  const acquireMutate = acquireMut.mutate
  useEffect(() => {
    if (!status?.owned_by_me) return
    if (secondsLeft === null || secondsLeft <= 0) return
    if (secondsLeft >= RENEW_THRESHOLD_S) return
    if (Date.now() - lastRenewAt.current < RENEW_RETRY_S * 1000) return
    lastRenewAt.current = Date.now()
    acquireMutate()
  }, [secondsLeft, status?.owned_by_me, acquireMutate])

  // ── Слушатель потери лока с бэка (423) ──────────────────────────────────
  useEffect(() => {
    const handler = () => {
      const prev = useRuleLockStore.getState().status
      if (prev) setStatus({ ...prev, owned_by_me: false })
      toast.error('Редактирование правил: лок утрачен. Войди заново.')
      void queryClient.invalidateQueries({ queryKey: LOCK_QUERY_KEY })
    }
    window.addEventListener('rule-lock-lost', handler)
    return () => window.removeEventListener('rule-lock-lost', handler)
  }, [queryClient, setStatus])

  // ── Освобождение на закрытие вкладки / unmount ──────────────────────────
  useEffect(() => {
    const releaseIfMine = () => {
      const s = useRuleLockStore.getState().status
      if (!s?.owned_by_me) return
      const token = useAuthStore.getState().accessToken
      if (!token) return
      const base = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'
      // keepalive — единственный способ дослать DELETE с заголовком при beforeunload
      void fetch(`${base}/admin/rules/lock`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
        keepalive: true,
      }).catch(() => undefined)
    }
    window.addEventListener('beforeunload', releaseIfMine)
    return () => {
      window.removeEventListener('beforeunload', releaseIfMine)
      releaseIfMine()
    }
  }, [])

  return {
    status,
    isLoading: statusQuery.isLoading,
    secondsLeft,
    acquire: acquireMut.mutate,
    isAcquiring: acquireMut.isPending,
    release: releaseMut.mutate,
    isReleasing: releaseMut.isPending,
    forceRelease: forceReleaseMut.mutate,
    isForceReleasing: forceReleaseMut.isPending,
    canEdit: status?.owned_by_me === true,
    isLockedByOther: status?.is_locked === true && status.owned_by_me === false,
  }
}
