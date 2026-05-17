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

  // Точечный апдейт кеша списком — без invalidate, чтобы форма не мерцала
  // на refetch (RuleForm reset завязан на rule из этого кеша).
  const upsertInList = (item: Rule) => {
    queryClient.setQueryData<Rule[]>(RULES_KEY, (old) =>
      old ? old.map((r) => (r.id === item.id ? item : r)) : [item],
    )
  }

  const create = useMutation<Rule, Error, RuleCreate>({
    mutationKey: ['admin', 'rules', 'create'],
    mutationFn: rulesApi.create,
    onSuccess: (item) => {
      toast.success(`Правило R-${item.number} создано`)
      queryClient.setQueryData<Rule[]>(RULES_KEY, (old) =>
        old ? [...old, item] : [item],
      )
    },
    onError: (err) => toast.error(err.message || 'Не удалось создать правило'),
  })

  const update = useMutation<Rule, Error, { id: string; body: RuleUpdate }>({
    mutationKey: ['admin', 'rules', 'update'],
    mutationFn: ({ id, body }) => rulesApi.update(id, body),
    onSuccess: (item) => {
      toast.success(`R-${item.number} сохранено`)
      upsertInList(item)
    },
    onError: (err) => toast.error(err.message || 'Не удалось сохранить правило'),
  })

  const remove = useMutation<void, Error, string>({
    mutationKey: ['admin', 'rules', 'delete'],
    mutationFn: rulesApi.delete,
    onSuccess: (_, id) => {
      toast.success('Правило удалено')
      queryClient.setQueryData<Rule[]>(RULES_KEY, (old) =>
        old ? old.filter((r) => r.id !== id) : old,
      )
    },
    onError: (err) => toast.error(err.message || 'Не удалось удалить правило'),
  })

  const publish = useMutation<Rule, Error, string>({
    mutationKey: ['admin', 'rules', 'publish'],
    mutationFn: rulesApi.publish,
    onSuccess: (item) => {
      toast.success(`R-${item.number} опубликовано`)
      upsertInList(item)
    },
    onError: (err) => toast.error(err.message || 'Не удалось опубликовать'),
  })

  const unpublish = useMutation<Rule, Error, string>({
    mutationKey: ['admin', 'rules', 'unpublish'],
    mutationFn: rulesApi.unpublish,
    onSuccess: (item) => {
      toast.success(`R-${item.number} снято с публикации`)
      upsertInList(item)
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
