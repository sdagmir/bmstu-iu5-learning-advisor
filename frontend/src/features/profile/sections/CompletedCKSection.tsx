import { memo, useMemo } from 'react'
import { Check } from '@phosphor-icons/react'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { CollapsibleGroup } from '@/components/common/CollapsibleGroup'
import { useCkCourses } from '@/features/catalog/useCatalog'
import { useCompletedCK } from '@/features/profile/useCompletedCK'
import { CK_CATEGORY_LABELS } from '@/constants/enums'
import { cn } from '@/lib/utils'
import type { CKCourse, CKCourseCategory } from '@/types/api'

/**
 * X5–X8 — пройденные программы ЦК. Группы по категории — раскрывающиеся,
 * прогресс-счётчик в шапке.
 *
 * Каждая карточка курса — memo'd `CKRow`. Стабильный `toggle` (useCallback в
 * useCompletedCK) + примитивный prop `isOn` (boolean из completedSet) →
 * клик по одной карточке НЕ ре-рендерит соседние строки. Никаких миганий.
 */
export function CompletedCKSection() {
  const coursesQuery = useCkCourses()
  const { completedSet, toggle } = useCompletedCK()

  const grouped = useMemo(() => {
    if (!coursesQuery.data) return [] as Array<[CKCourseCategory, CKCourse[]]>
    const map = new Map<CKCourseCategory, CKCourse[]>()
    for (const c of coursesQuery.data) {
      const list = map.get(c.category) ?? []
      list.push(c)
      map.set(c.category, list)
    }
    return Array.from(map.entries())
  }, [coursesQuery.data])

  return (
    <div className="flex flex-col gap-[var(--space-base)]">
      <div className="flex flex-col gap-[var(--space-xs)]">
        <Label>Пройденные программы ЦК</Label>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Отметь программы цифровой кафедры, которые ты уже прошёл. Это влияет на то, какие новые
          ЦК-курсы система предложит.
        </p>
      </div>

      {coursesQuery.isLoading ? (
        <CKSkeleton />
      ) : grouped.length === 0 ? (
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
          Каталог программ пока пуст.
        </p>
      ) : (
        <div className="flex flex-col gap-[var(--space-sm)]">
          {grouped.map(([category, courses]) => {
            const checked = courses.filter((c) => completedSet.has(c.id)).length
            return (
              <CollapsibleGroup
                key={category}
                title={CK_CATEGORY_LABELS[category]}
                meta={`${checked} / ${courses.length}`}
              >
                <div className="flex flex-col">
                  {courses.map((course) => (
                    <CKRow
                      key={course.id}
                      course={course}
                      isOn={completedSet.has(course.id)}
                      onToggle={toggle}
                    />
                  ))}
                </div>
              </CollapsibleGroup>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface CKRowProps {
  course: CKCourse
  isOn: boolean
  onToggle: (course: CKCourse) => void
}

const CKRow = memo(function CKRow({ course, isOn, onToggle }: CKRowProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(course)}
      aria-pressed={isOn}
      className={cn(
        'flex w-full items-start gap-[var(--space-md)] rounded-[6px] px-[var(--space-base)] py-[var(--space-sm)] text-left transition-colors',
        isOn ? 'text-[color:var(--color-text)]' : 'text-[color:var(--color-text-muted)]',
        'hover:bg-[color:var(--color-surface-muted)]',
      )}
    >
      <span
        className={cn(
          'mt-[2px] flex h-5 w-5 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
          isOn
            ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary)] text-[color:var(--color-surface)]'
            : 'border-[color:var(--color-border)] bg-transparent',
        )}
        aria-hidden
      >
        {isOn && <Check size={12} weight="bold" />}
      </span>
      <span className="flex flex-col gap-[2px]">
        <span className={cn('text-[length:var(--text-base)]', isOn && 'font-medium')}>
          {course.name}
        </span>
        {course.description && (
          <span className="line-clamp-1 text-[length:var(--text-xs)] text-[color:var(--color-text-subtle)]">
            {course.description}
          </span>
        )}
      </span>
    </button>
  )
})

function CKSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      {[3, 4].map((rows, i) => (
        <div key={i} className="flex flex-col gap-[var(--space-sm)]">
          <Skeleton className="h-3 w-32" />
          <div className="flex flex-col gap-[var(--space-sm)]">
            {Array.from({ length: rows }).map((_, j) => (
              <div key={j} className="flex items-center gap-[var(--space-md)]">
                <Skeleton className="h-5 w-5" />
                <Skeleton className="h-4 flex-1" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
