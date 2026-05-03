import { useMemo, useState } from 'react'
import { LockOpen, LockKey, Warning, CircleNotch } from '@phosphor-icons/react'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { cn } from '@/lib/utils'
import type { RuleEditingLockStatus } from '@/types/api'

interface RulesLockHeaderProps {
  status: RuleEditingLockStatus | null
  secondsLeft: number | null
  isAcquiring: boolean
  isReleasing: boolean
  isForceReleasing: boolean
  onAcquire: () => void
  onRelease: () => void
  onForceRelease: () => void
}

/** mm:ss из секунд. Используется только когда лок мой. */
function formatTime(s: number | null): string {
  if (s === null || s < 0) return '--:--'
  const mm = Math.floor(s / 60)
  const ss = s % 60
  return `${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}`
}

function formatExpiresAt(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })
}

/**
 * Sticky-шапка над списком правил: показывает состояние лока и даёт
 * единственное правильное действие в каждый момент.
 *
 * Состояния:
 *  - `null` (загрузка) — спиннер, бездействие
 *  - свободно — primary CTA «Войти в редактор»
 *  - мой — таймер mm:ss (≤5 мин жёлтый + «автопродление…») + ghost «Выйти»
 *  - чужой — бейдж занятости + ghost «Принудительно освободить»
 */
export function RulesLockHeader({
  status,
  secondsLeft,
  isAcquiring,
  isReleasing,
  isForceReleasing,
  onAcquire,
  onRelease,
  onForceRelease,
}: RulesLockHeaderProps) {
  const [forceOpen, setForceOpen] = useState(false)

  const inWarn = useMemo(
    () => secondsLeft !== null && secondsLeft > 0 && secondsLeft < 300,
    [secondsLeft],
  )

  // 1) загрузка
  if (!status) {
    return (
      <Header>
        <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          <CircleNotch size={14} className="animate-spin" />
          Проверяем статус редактора…
        </span>
      </Header>
    )
  }

  // 4) лок чужой
  if (status.is_locked && !status.owned_by_me) {
    return (
      <>
        <Header>
          <span className="flex min-w-0 items-center gap-[var(--space-sm)] text-[length:var(--text-sm)]">
            <LockKey
              size={16}
              weight="regular"
              className="text-[color:var(--color-warning)]"
            />
            <span className="truncate">
              <span className="text-[color:var(--color-text)]">Редактирует</span>{' '}
              <span className="font-medium text-[color:var(--color-text)]">
                {status.admin_email ?? 'другой админ'}
              </span>
              {status.expires_at && (
                <span className="text-[color:var(--color-text-muted)]">
                  {' '}
                  · до {formatExpiresAt(status.expires_at)}
                </span>
              )}
            </span>
          </span>
          <div className="ml-auto flex items-center gap-[var(--space-sm)]">
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setForceOpen(true)}
                  disabled={isForceReleasing}
                >
                  <Warning size={14} weight="regular" />
                  Принудительно освободить
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                Заберёт лок у текущего редактора. Его несохранённые правки могут
                потеряться.
              </TooltipContent>
            </Tooltip>
          </div>
        </Header>
        <ConfirmDialog
          open={forceOpen}
          onOpenChange={setForceOpen}
          title="Освободить чужой лок?"
          description={`Сейчас правила редактирует ${status.admin_email ?? 'другой админ'}. Если он не сохранит изменения, они будут потеряны.`}
          confirmLabel="Освободить"
          variant="danger"
          loading={isForceReleasing}
          onConfirm={() => {
            onForceRelease()
            setForceOpen(false)
          }}
        />
      </>
    )
  }

  // 3) лок мой
  if (status.owned_by_me) {
    return (
      <Header>
        <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)]">
          <LockKey
            size={16}
            weight="bold"
            className={cn(
              inWarn ? 'text-[color:var(--color-warning)]' : 'text-[color:var(--color-success)]',
            )}
          />
          <span className="text-[color:var(--color-text)]">Редактор открыт</span>
          <span
            className={cn(
              'font-mono tabular-nums',
              inWarn
                ? 'text-[color:var(--color-warning)]'
                : 'text-[color:var(--color-text-muted)]',
            )}
            aria-label={`Осталось ${formatTime(secondsLeft)}`}
          >
            {formatTime(secondsLeft)}
          </span>
          {inWarn && (
            <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
              автопродление…
            </span>
          )}
        </span>
        <div className="ml-auto">
          <Button
            variant="ghost"
            size="sm"
            onClick={onRelease}
            disabled={isReleasing}
          >
            Выйти из редактора
          </Button>
        </div>
      </Header>
    )
  }

  // 2) свободно
  return (
    <Header>
      <span className="flex items-center gap-[var(--space-sm)] text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
        <LockOpen size={16} weight="regular" />
        Редактор свободен — войди, чтобы вносить изменения
      </span>
      <div className="ml-auto">
        <Button size="sm" onClick={onAcquire} disabled={isAcquiring}>
          {isAcquiring ? (
            <CircleNotch size={14} className="animate-spin" />
          ) : (
            <LockKey size={14} weight="regular" />
          )}
          Войти в редактор
        </Button>
      </div>
    </Header>
  )
}

function Header({ children }: { children: React.ReactNode }) {
  return (
    <div className="sticky top-0 z-20 flex items-center gap-[var(--space-base)] border-b border-[color:var(--color-border)] bg-[color:var(--color-bg)] px-[var(--space-2xl)] py-[var(--space-md)]">
      {children}
    </div>
  )
}
