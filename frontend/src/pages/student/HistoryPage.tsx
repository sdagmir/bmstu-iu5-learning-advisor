import { Link } from 'react-router-dom'
import { ClockCounterClockwise } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { routes } from '@/constants/routes'

/**
 * Заглушка раздела «История». Лента прошлых рекомендаций появится, когда
 * бэк начнёт сохранять snapshots при изменении профиля
 * (`GET /expert/recommendations/history`, см. docs/TODO.md).
 */
export default function HistoryPage() {
  return (
    <>
      <PageTopBar title="История" />
      <div className="mx-auto flex max-w-[600px] flex-col items-center gap-[var(--space-lg)] px-[var(--space-2xl)] py-[var(--space-3xl)] text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[color:var(--color-primary-soft)] text-[color:var(--color-primary)]">
          <ClockCounterClockwise size={24} weight="regular" />
        </div>
        <div className="flex flex-col gap-[var(--space-sm)]">
          <h1 className="font-serif text-[length:var(--text-xl)] font-semibold text-[color:var(--color-text)]">
            История рекомендаций готовится
          </h1>
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            Когда ты будешь обновлять профиль, система начнёт сохранять снимки
            рекомендаций. Здесь можно будет посмотреть, как они менялись со
            временем.
          </p>
          <p className="text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            Текущие актуальные рекомендации — на главной.
          </p>
        </div>
        <Button asChild variant="outline">
          <Link to={routes.home}>На главную</Link>
        </Button>
      </div>
    </>
  )
}
