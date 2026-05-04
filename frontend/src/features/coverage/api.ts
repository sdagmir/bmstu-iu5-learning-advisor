import { apiFetch } from '@/lib/api-client'
import type { CoverageResponse } from '@/types/api'

export const coverageApi = {
  me: () => apiFetch<CoverageResponse>('/users/me/coverage'),
}
