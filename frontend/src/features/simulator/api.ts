import { apiFetch } from '@/lib/api-client'
import type { EvaluateDebugResponse, SimulatorProfile } from '@/types/api'

export const simulatorApi = {
  /** Прогон профиля через ЭС с трассировкой по 52 правилам. Только admin. */
  evaluateDebug: (profile: SimulatorProfile) =>
    apiFetch<EvaluateDebugResponse>('/expert/evaluate/debug', {
      method: 'POST',
      body: JSON.stringify(profile),
    }),
}
