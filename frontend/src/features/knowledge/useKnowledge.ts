import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { knowledgeApi } from './api'
import type {
  RagDocumentChunk,
  RagDocumentUpload,
  RagSearchRequest,
} from '@/types/api'

const STATS_KEY = ['admin', 'rag', 'stats'] as const

export function useRagStats() {
  return useQuery({
    queryKey: STATS_KEY,
    queryFn: knowledgeApi.stats,
    staleTime: 30_000,
  })
}

export function useRagSearch() {
  return useMutation<RagDocumentChunk[], Error, RagSearchRequest>({
    mutationKey: ['admin', 'rag', 'search'],
    mutationFn: knowledgeApi.search,
    onError: (err) => toast.error(err.message || 'Поиск не удался'),
  })
}

export function useRagUpload() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ['admin', 'rag', 'upload'],
    mutationFn: (body: RagDocumentUpload) => knowledgeApi.upload(body),
    onSuccess: (data) => {
      toast.success(`Документ «${data.source}» проиндексирован: ${data.chunks_count} чанков`)
      void queryClient.invalidateQueries({ queryKey: STATS_KEY })
    },
    onError: (err: Error) => toast.error(err.message || 'Не удалось загрузить документ'),
  })
}

export function useRagDelete() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ['admin', 'rag', 'delete'],
    mutationFn: (source: string) => knowledgeApi.delete(source),
    onSuccess: (_, source) => {
      toast.success(`Документ «${source}» удалён`)
      void queryClient.invalidateQueries({ queryKey: STATS_KEY })
    },
    onError: (err: Error) => toast.error(err.message || 'Не удалось удалить документ'),
  })
}
