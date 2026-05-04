import { apiFetch } from '@/lib/api-client'
import type {
  RagDocumentChunk,
  RagDocumentSummary,
  RagDocumentUpload,
  RagDocumentUploadResult,
  RagSearchRequest,
  RagStats,
} from '@/types/api'

/** Тонкая обёртка над `/rag/**`. */
export const knowledgeApi = {
  search: (body: RagSearchRequest) =>
    apiFetch<RagDocumentChunk[]>('/rag/search', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  list: (offset = 0, limit = 50) =>
    apiFetch<RagDocumentSummary[]>(`/rag/documents?offset=${offset}&limit=${limit}`),
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
