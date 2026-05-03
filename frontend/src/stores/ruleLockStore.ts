import { create } from 'zustand'
import type { RuleEditingLockStatus } from '@/types/api'

interface RuleLockState {
  status: RuleEditingLockStatus | null
  setStatus: (s: RuleEditingLockStatus | null) => void
}

/**
 * Лёгкий стор последнего известного статуса лока. Не персистится —
 * при перезагрузке вкладки всё равно делаем GET /lock на mount.
 *
 * `secondsLeft` НЕ хранится здесь: вычисляем в `useRuleLock` из
 * `expires_at` + локального тика, чтобы счётчик не зависел от того
 * сколько времени стор пролежал в памяти между ре-рендерами.
 */
export const useRuleLockStore = create<RuleLockState>((set) => ({
  status: null,
  setStatus: (status) => set({ status }),
}))
