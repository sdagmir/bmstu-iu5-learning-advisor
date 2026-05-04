import { apiFetch } from '@/lib/api-client'
import type { RecommendationSnapshot } from '@/types/api'

export const historyApi = {
  list: (offset = 0, limit = 50) =>
    apiFetch<RecommendationSnapshot[]>(
      `/expert/recommendations/history?offset=${offset}&limit=${limit}`,
    ),
}
