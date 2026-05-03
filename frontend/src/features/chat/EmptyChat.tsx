import { InputBar } from './InputBar'

interface EmptyChatProps {
  onSend: (text: string) => void
  isPending: boolean
}

const SUGGESTIONS: string[] = [
  'Какой курс ЦК взять на следующем семестре?',
  'Подходит ли мне ML-трек Технопарка?',
  'На что упор в курсовой по моей цели?',
]

/**
 * Пустое состояние чата — hero-композиция: приветствие в центре, под ним
 * крупный input, под input — chip-подсказки. Сам InputBar в варианте `hero`,
 * никакого sticky-бара внизу страницы.
 */
export function EmptyChat({ onSend, isPending }: EmptyChatProps) {
  return (
    <div className="flex w-full max-w-[640px] flex-col gap-[var(--space-xl)]">
      <div className="flex flex-col items-center gap-[var(--space-sm)] text-center">
        <h2 className="font-serif text-[length:var(--text-2xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
          Спроси меня о траектории
        </h2>
        <p className="max-w-[480px] text-[length:var(--text-base)] leading-relaxed text-[color:var(--color-text-muted)]">
          Я знаю твой профиль, учебный план ИУ5 и 52 правила экспертной системы. Могу предложить
          курсы ЦК, трек Технопарка, темы курсовых.
        </p>
      </div>

      <InputBar onSend={onSend} isPending={isPending} />

      <div className="flex flex-wrap justify-center gap-[var(--space-xs)]">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSend(s)}
            disabled={isPending}
            className="cursor-pointer rounded-full border border-[color:var(--color-border)] bg-[color:var(--color-surface)] px-[var(--space-base)] py-[6px] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)] transition-colors hover:border-[color:var(--color-primary)] hover:text-[color:var(--color-primary)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}
