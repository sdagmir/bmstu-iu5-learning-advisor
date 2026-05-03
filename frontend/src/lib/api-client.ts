import { useAuthStore } from '@/stores/authStore'
import type { ApiErrorBody, TokenPair, ValidationErrorBody } from '@/types/api'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

/**
 * Доменная ошибка бэка (все 4xx/5xx кроме 422 и 423).
 * Поле `code` — из таблицы в API_REFERENCE.md.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

/** Pydantic 422 — детализация по полям. */
export class ValidationError extends ApiError {
  readonly details: ValidationErrorBody['detail']
  constructor(details: ValidationErrorBody['detail']) {
    super(422, 'ValidationError', 'Ошибка валидации данных')
    this.name = 'ValidationError'
    this.details = details
  }
}

/**
 * 423 Locked — лок на редактирование правил ЭС утрачен или не захвачен.
 * Срабатывает только для `/admin/rules/**`.
 */
export class LockLostError extends ApiError {
  constructor(message: string) {
    super(423, 'Locked', message)
    this.name = 'LockLostError'
  }
}

type FetchInit = Omit<RequestInit, 'body'> & { body?: BodyInit | null }

function buildUrl(path: string): string {
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  const normalized = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalized}`
}

async function parseError(response: Response): Promise<never> {
  if (response.status === 422) {
    const body = (await response.json().catch(() => null)) as ValidationErrorBody | null
    throw new ValidationError(body?.detail ?? [])
  }
  if (response.status === 423) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null
    const msg = body?.error?.message ?? 'Лок на редактирование правил утрачен'
    const err = new LockLostError(msg)
    // Глобальный сигнал для useRuleLock — фаза 7
    window.dispatchEvent(new CustomEvent('rule-lock-lost', { detail: { message: msg } }))
    throw err
  }
  const body = (await response.json().catch(() => null)) as ApiErrorBody | null
  const code = body?.error?.code ?? 'UnknownError'
  const message = body?.error?.message ?? response.statusText
  throw new ApiError(response.status, code, message)
}

let refreshInFlight: Promise<TokenPair> | null = null

async function refreshAccessToken(): Promise<TokenPair> {
  const { refreshToken, clear } = useAuthStore.getState()
  if (!refreshToken) {
    clear()
    throw new ApiError(401, 'UnauthorizedError', 'Нет refresh-токена')
  }

  // Дедупликация: если уже идёт refresh — ждём его
  if (refreshInFlight) return refreshInFlight

  refreshInFlight = (async () => {
    const response = await fetch(buildUrl('/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!response.ok) {
      clear()
      throw new ApiError(401, 'UnauthorizedError', 'Не удалось обновить токен')
    }
    const pair = (await response.json()) as TokenPair
    const user = useAuthStore.getState().user
    if (user) {
      useAuthStore
        .getState()
        .setSession({ access: pair.access_token, refresh: pair.refresh_token }, user)
    }
    return pair
  })()

  try {
    return await refreshInFlight
  } finally {
    refreshInFlight = null
  }
}

/**
 * Центральный fetch-wrapper. Авто-подставляет Authorization, на 401 делает
 * один retry через /auth/refresh, парсит доменные ошибки в ApiError.
 */
export async function apiFetch<T>(path: string, init: FetchInit = {}): Promise<T> {
  const doRequest = async (token: string | null): Promise<Response> => {
    const headers = new Headers(init.headers)
    if (!headers.has('Content-Type') && init.body) {
      headers.set('Content-Type', 'application/json')
    }
    if (token) headers.set('Authorization', `Bearer ${token}`)
    return fetch(buildUrl(path), { ...init, headers })
  }

  const { accessToken } = useAuthStore.getState()
  let response = await doRequest(accessToken)

  if (response.status === 401 && accessToken) {
    try {
      const pair = await refreshAccessToken()
      response = await doRequest(pair.access_token)
    } catch {
      // refresh не удался — отдаём исходную 401
      return parseError(response)
    }
  }

  if (!response.ok) return parseError(response)

  if (response.status === 204) return undefined as T
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return undefined as T
  return (await response.json()) as T
}
