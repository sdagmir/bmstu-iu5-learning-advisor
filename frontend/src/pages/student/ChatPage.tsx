import { Plus, ArrowClockwise } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { useChatSession } from '@/features/chat/useChatSession'
import { ChatLent } from '@/features/chat/ChatLent'
import { InputBar } from '@/features/chat/InputBar'
import { EmptyChat } from '@/features/chat/EmptyChat'

/**
 * Чат-страница. Два режима по композиции:
 *
 *  - empty: hero-блок в центре — приветствие + крупный input + chip-подсказки.
 *  - active: лента сообщений + input снизу, без border-t разделителей —
 *    единое полотно (рамкой служит сам rounded-input).
 */
export default function ChatPage() {
  const { messages, send, retry, clear, isPending, canRetry } = useChatSession()
  const isEmpty = messages.length === 0

  return (
    <div className="flex h-full flex-col">
      <PageTopBar
        title="Чат"
        actions={
          <div className="flex items-center gap-[var(--space-xs)]">
            {canRetry && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={retry}
                    aria-label="Повторить отправку"
                  >
                    <ArrowClockwise size={14} weight="regular" />
                    Повторить
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Переотправить последний вопрос</TooltipContent>
              </Tooltip>
            )}
            {!isEmpty && (
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={clear}
                    aria-label="Начать новый диалог"
                  >
                    <Plus size={14} weight="regular" />
                    Новый диалог
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">Очистить историю</TooltipContent>
              </Tooltip>
            )}
          </div>
        }
      />

      {isEmpty ? (
        <div className="flex flex-1 flex-col items-center overflow-y-auto px-[var(--space-2xl)] pt-[clamp(64px,15vh,160px)] pb-[var(--space-2xl)]">
          <EmptyChat onSend={send} isPending={isPending} />
        </div>
      ) : (
        <>
          <ChatLent messages={messages} isPending={isPending} />
          <div className="px-[var(--space-2xl)] pt-[var(--space-sm)] pb-[var(--space-base)]">
            <div className="mx-auto w-full max-w-[720px]">
              <InputBar onSend={send} isPending={isPending} />
            </div>
          </div>
        </>
      )}
    </div>
  )
}
