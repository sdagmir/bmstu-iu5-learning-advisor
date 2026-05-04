import { apiFetch } from '@/lib/api-client'
import type {
  RagDocumentChunk,
  RagDocumentUpload,
  RagDocumentUploadResult,
  RagSearchRequest,
  RagStats,
} from '@/types/api'

/**
 * Тонкая обёртка над `/rag/**`. Список загруженных документов отдельным
 * эндпоинтом не доступен (TODO бэка) — поэтому DocumentList в UI пока нет.
 */
export const knowledgeApi = {
  search: (body: RagSearchRequest) =>
    apiFetch<RagDocumentChunk[]>('/rag/search', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  upload: (body: RagDocumentUpload) =>
    apiFetch<RagDocumentUploadResult>('/rag/documents', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  delete: (source: string) =>
    apiFetch<void>(`/rag/documents/${encodeURIComponent(source)}`, {
      method: 'DELETE',
    }),
  stats: () => apiFetch<RagStats>('/rag/stats'),
}
