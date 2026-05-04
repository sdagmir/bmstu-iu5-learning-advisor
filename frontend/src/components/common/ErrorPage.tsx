import { isRouteErrorResponse, useRouteError, useNavigate } from 'react-router-dom'
import { ArrowClockwise, House, Warning } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { routes } from '@/constants/routes'

/**
 * Универсальная страница ошибки для React Router. Подключается через
 * `errorElement` — ловит все исключения внутри роута, render-ошибки и
 * нештатные ответы 4xx/5xx от loader'ов.
 *
 * Без неё React Router в DEV-режиме показывает «Unexpected Application Error»
 * со стектрейсом, а в production — белый экран. Тут — человекочитаемый текст,
 * кнопка перезагрузки и возврат на главную.
 */
export function ErrorPage() {
  const error = useRouteError()
  const navigate = useNavigate()

  // Разбираем что прилетело: HTTP-ошибка от роута, обычный JS Error или что-то иное.
  let title = 'Что-то пошло не так'
  let detail: string | null = null

  if (isRouteErrorResponse(error)) {
    title = error.status === 404 ? 'Страница не найдена' : `Ошибка ${error.status}`
    detail = typeof error.data === 'string' ? error.data : (error.statusText ?? null)
  } else if (error instanceof Error) {
    detail = error.message
  } else if (typeof error === 'string') {
    detail = error
  }

  return (
    <div className="flex min-h-svh items-center justify-center px-[var(--space-base)]">
      <div className="flex max-w-[480px] flex-col items-center gap-[var(--space-lg)] text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--color-danger-soft)] text-[color:var(--color-danger)]">
          <Warning size={24} weight="regular" />
        </div>
        <div className="flex flex-col gap-[var(--space-sm)]">
          <h1 className="font-serif text-[length:var(--text-xl)] font-semibold text-[color:var(--color-text)]">
            {title}
          </h1>
          {detail && (
            <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
              {detail}
            </p>
          )}
          <p className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Если ошибка повторяется — перезагрузи страницу или вернись на главную.
          </p>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-[var(--space-sm)]">
          <Button onClick={() => window.location.reload()}>
            <ArrowClockwise size={14} />
            Перезагрузить
          </Button>
          <Button variant="outline" onClick={() => navigate(routes.home)}>
            <House size={14} />
            На главную
          </Button>
        </div>
      </div>
    </div>
  )
}
