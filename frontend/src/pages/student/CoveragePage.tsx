import { Link } from 'react-router-dom'
import { Hourglass } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { routes } from '@/constants/routes'

/**
 * Заглушка раздела «Покрытие». Визуализация радара компетенций «имеешь vs
 * нужно» появится, когда бэк отдаст `GET /users/me/coverage` (см. docs/TODO.md).
 */
export default function CoveragePage() {
  return (
    <>
      <PageTopBar title="Покрытие" />
      <div className="mx-auto flex max-w-[600px] flex-col items-center gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-3xl)] text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--color-primary-soft)] text-[color:var(--color-primary)]">
          <Hourglass size={24} weight="regular" />
        </div>
        <div className="flex flex-col gap-[var(--space-sm)]">
          <h1 className="font-serif text-[length:var(--text-xl)] font-semibold text-[color:var(--color-text)]">
            Радар компетенций готовится
          </h1>
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            Скоро здесь появится визуализация: какие компетенции у тебя уже
            есть, а какие нужно подтянуть под выбранную карьерную цель.
          </p>
          <p className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Пока что рекомендации из ЭС доступны на главной — там видно, какие
            пробелы они закрывают.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to={routes.home}>На главную</Link>
        </Button>
      </div>
    </>
  )
}
