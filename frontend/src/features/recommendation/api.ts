import { apiFetch } from '@/lib/api-client'
import type { Recommendation } from '@/types/api'

export const recommendationApi = {
  /** Рекомендации для текущего пользователя. Профиль X1–X12 вычисляется бэком. */
  getMy: () => apiFetch<Recommendation[]>('/expert/my-recommendations'),
}
