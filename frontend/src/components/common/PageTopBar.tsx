import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageTopBarProps {
  /** Подпись секции — `Профиль`, `Дашборд`, `Симулятор`. Короткая. */
  title: string
  /** Иконка секции (Phosphor 18px). Совпадает с иконкой в sidebar nav. */
  icon?: ReactNode
  /** Слот для интерактивов: статус сохранения, primary-кнопка, фильтр и т.п. */
  actions?: ReactNode
}

/**
 * Sticky-шапка страницы. Анкер «где я» — остаётся видимой при скролле контента.
 *
 * Bg = page bg (`--color-bg`) — топбар сливается с фоном страницы и контент
 * НЕ просвечивает сквозь него (это не «эффект», это базовая корректность
 * sticky-хедера). Никаких glass/backdrop-blur — против бренда.
 *
 * Граница появляется по скроллу («earn the line», Emil Kowalski) — пока контент
 * на верхушке, топбар сливается со страницей; как только проскроллили — fade-in
 * тонкий border-bottom как тихий сигнал «контент уехал». Скролл-листенер на
 * родительском `<main>`, который и есть наш скролл-контейнер.
 */
export function PageTopBar({ title, icon, actions }: PageTopBarProps) {
  const stickyRef = useRef<HTMLDivElement>(null)
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const sticky = stickyRef.current
    if (!sticky) return
    const main = sticky.closest('main')
    if (!main) return

    const handleScroll = () => setScrolled(main.scrollTop > 0)
    handleScroll()
    main.addEventListener('scroll', handleScroll, { passive: true })
    return () => main.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <div
      ref={stickyRef}
      className={cn(
        'sticky top-0 z-10 border-b bg-[color:var(--color-bg)] transition-[border-color] duration-150',
        scrolled
          ? 'border-[color:var(--color-border)]'
          : 'border-transparent',
      )}
    >
      <div className="flex items-center justify-between gap-[var(--space-base)] px-[var(--space-2xl)] py-[var(--space-base)]">
        <div className="flex min-w-0 items-center gap-[var(--space-sm)]">
          {icon ? (
            <span className="shrink-0 text-[color:var(--color-text-muted)]">{icon}</span>
          ) : null}
          <span className="truncate font-serif text-[length:var(--text-md)] font-semibold tracking-tight text-[color:var(--color-text)]">
            {title}
          </span>
        </div>
        {actions ? (
          <div className="flex shrink-0 items-center gap-[var(--space-sm)]">{actions}</div>
        ) : null}
      </div>
    </div>
  )
}
