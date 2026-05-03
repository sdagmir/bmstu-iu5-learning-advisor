import { cn } from '@/lib/utils'

/**
 * Минимальный текстовый лого. Слитный цвет, серифная Bitter,
 * лёгкий negative tracking — анкер сайдбара, а не «вёрстанный заголовок».
 * Когда появится векторный знак — заменим тут.
 */
export function Logo({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'font-serif text-[length:var(--text-md)] font-semibold tracking-tight text-[color:var(--color-text)]',
        className,
      )}
    >
      РС ИТО
    </div>
  )
}
