import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'

interface MarkdownContentProps {
  content: string
  className?: string
}

/**
 * Безопасный markdown-рендер для сообщений LLM. Используется в обычном
 * чате студента и в admin debug-чате.
 *
 * Поддерживает: bold/italic, списки (нумерованные и маркированные),
 * inline-код, code blocks, ссылки, заголовки, таблицы (через remark-gfm).
 *
 * Стили — наши токены типографики и spacing'а; ничего «дефолтно-markdown'ного»
 * (огромные h1, синие подчёркнутые ссылки) — всё в нашем визуальном языке.
 */
export function MarkdownContent({ content, className }: MarkdownContentProps) {
  return (
    <div
      className={cn(
        'flex flex-col gap-[var(--space-sm)] text-[length:var(--text-base)] leading-relaxed text-[color:var(--color-text)]',
        '[&_p]:m-0',
        '[&_strong]:font-semibold [&_strong]:text-[color:var(--color-text)]',
        '[&_em]:italic',
        '[&_a]:text-[color:var(--color-primary)] [&_a]:underline-offset-2 hover:[&_a]:underline',
        '[&_ul]:m-0 [&_ul]:flex [&_ul]:list-disc [&_ul]:flex-col [&_ul]:gap-[var(--space-xs)] [&_ul]:pl-[var(--space-lg)]',
        '[&_ol]:m-0 [&_ol]:flex [&_ol]:list-decimal [&_ol]:flex-col [&_ol]:gap-[var(--space-xs)] [&_ol]:pl-[var(--space-lg)]',
        '[&_li]:m-0',
        '[&_h1]:m-0 [&_h1]:font-serif [&_h1]:text-[length:var(--text-lg)] [&_h1]:font-semibold',
        '[&_h2]:m-0 [&_h2]:font-serif [&_h2]:text-[length:var(--text-md)] [&_h2]:font-semibold',
        '[&_h3]:m-0 [&_h3]:text-[length:var(--text-base)] [&_h3]:font-semibold',
        '[&_code]:rounded-[4px] [&_code]:bg-[color:var(--color-surface-muted)] [&_code]:px-[6px] [&_code]:py-[1px] [&_code]:font-mono [&_code]:text-[length:var(--text-sm)]',
        '[&_pre]:overflow-x-auto [&_pre]:rounded-[6px] [&_pre]:bg-[color:var(--color-surface-muted)] [&_pre]:p-[var(--space-md)] [&_pre]:font-mono [&_pre]:text-[length:var(--text-sm)] [&_pre]:leading-relaxed',
        '[&_pre_code]:rounded-none [&_pre_code]:bg-transparent [&_pre_code]:p-0',
        '[&_blockquote]:border-l-2 [&_blockquote]:border-[color:var(--color-border-strong)] [&_blockquote]:pl-[var(--space-base)] [&_blockquote]:text-[color:var(--color-text-muted)]',
        '[&_hr]:my-[var(--space-sm)] [&_hr]:border-[color:var(--color-border)]',
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}
