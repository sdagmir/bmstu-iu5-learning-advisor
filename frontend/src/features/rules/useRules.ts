import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { rulesApi } from './api'
import type {
  Rule,
  RuleCreate,
  RulePreviewRequest,
  RulePreviewResponse,
  RuleUpdate,
} from '@/types/api'

const RULES_KEY = ['admin', 'rules'] as const

/** Список всех правил + мутации create/update/delete/publish/unpublish. */
export function useRules() {
  const queryClient = useQueryClient()

  const list = useQuery({
    queryKey: RULES_KEY,
    queryFn: rulesApi.list,
    staleTime: 30_000,
  })

  const invalidate = () => queryClient.invalidateQueries({ queryKey: RULES_KEY })

  const create = useMutation<Rule, Error, RuleCreate>({
    mutationKey: ['admin', 'rules', 'create'],
    mutationFn: rulesApi.create,
    onSuccess: (item) => {
      toast.success(`Правило R-${item.number} создано`)
      void invalidate()
    },
    onError: (err) => toast.error(err.message || 'Не удалось создать правило'),
  })

  const update = useMutation<Rule, Error, { id: string; body: RuleUpdate }>({
    mutationKey: ['admin', 'rules', 'update'],
    mutationFn: ({ id, body }) => rulesApi.update(id, body),
    onSuccess: (item) => {
      toast.success(`R-${item.number} сохранено`)
      void invalidate()
    },
    onError: (err) => toast.error(err.message || 'Не удалось сохранить правило'),
  })

  const remove = useMutation<void, Error, string>({
    mutationKey: ['admin', 'rules', 'delete'],
    mutationFn: rulesApi.delete,
    onSuccess: () => {
      toast.success('Правило удалено')
      void invalidate()
    },
    onError: (err) => toast.error(err.message || 'Не удалось удалить правило'),
  })

  const publish = useMutation<Rule, Error, string>({
    mutationKey: ['admin', 'rules', 'publish'],
    mutationFn: rulesApi.publish,
    onSuccess: (item) => {
      toast.success(`R-${item.number} опубликовано`)
      void invalidate()
    },
    onError: (err) => toast.error(err.message || 'Не удалось опубликовать'),
  })

  const unpublish = useMutation<Rule, Error, string>({
    mutationKey: ['admin', 'rules', 'unpublish'],
    mutationFn: rulesApi.unpublish,
    onSuccess: (item) => {
      toast.success(`R-${item.number} снято с публикации`)
      void invalidate()
    },
    onError: (err) => toast.error(err.message || 'Не удалось снять с публикации'),
  })

  return { list, create, update, remove, publish, unpublish }
}

/** Sandbox preview — отдельная мутация, чтобы не путалась с CRUD-кешем. */
export function useRulePreview() {
  return useMutation<RulePreviewResponse, Error, RulePreviewRequest>({
    mutationKey: ['admin', 'rules', 'preview'],
    mutationFn: rulesApi.preview,
    onError: (err) => toast.error(err.message || 'Preview не удался'),
  })
}
