import { memo, useMemo } from 'react'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { CollapsibleGroup } from '@/components/common/CollapsibleGroup'
import { useDisciplines } from '@/features/catalog/useCatalog'
import { useGrades } from '@/features/profile/useGrades'
import { useAuthStore } from '@/stores/authStore'
import type { Discipline } from '@/types/api'

const NONE_VALUE = '__none__'
const GRADE_OPTIONS = [2, 3, 4, 5] as const

/**
 * X9–X10 — оценки по дисциплинам. Показываем только пройденные семестры
 * (`current_semester - 1`). Группы раскрывающиеся, прогресс-счётчик в шапке.
 *
 * Каждая строка — memo'd `GradeRow`. С `setGrade` стабильным (через useCallback
 * в useGrades) — строка ре-рендерится ТОЛЬКО когда меняется ЕЁ оценка, не
 * соседних. Соседние Select'ы и иконки в них не дёргаются.
 */
export function GradesSection() {
  const semester = useAuthStore((s) => s.user?.semester ?? null)
  const semesterMax = semester != null ? semester - 1 : 8
  const disciplinesQuery = useDisciplines(semesterMax)
  const { grades, setGrade } = useGrades()

  // Map для O(1) lookup оценки по discipline_id — иначе на каждой строке O(n) filter.
  const gradeByDisciplineId = useMemo(() => {
    const map = new Map<string, number>()
    for (const g of grades) map.set(g.discipline_id, g.grade)
    return map
  }, [grades])

  const groupedBySemester = useMemo(() => {
    if (!disciplinesQuery.data) return [] as Array<[number, Discipline[]]>
    const map = new Map<number, Discipline[]>()
    for (const d of disciplinesQuery.data) {
      const list = map.get(d.semester) ?? []
      list.push(d)
      map.set(d.semester, list)
    }
    return Array.from(map.entries()).sort(([a], [b]) => a - b)
  }, [disciplinesQuery.data])

  return (
    <div className="flex flex-col gap-[var(--space-base)]">
      <div className="flex flex-col gap-[var(--space-xs)]">
        <Label>Оценки по дисциплинам</Label>
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
          Система использует средние оценки чтобы понять, где у тебя пробелы. Текущий семестр в
          процессе и ещё не учитывается.
        </p>
      </div>

      {disciplinesQuery.isLoading ? (
        <GradesSkeleton />
      ) : groupedBySemester.length === 0 ? (
        <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-subtle)]">
          Пока нет пройденных семестров — оценки появятся после окончания первого.
        </p>
      ) : (
        <div className="flex flex-col gap-[var(--space-sm)]">
          {groupedBySemester.map(([sem, disciplines]) => {
            const filled = disciplines.filter((d) => gradeByDisciplineId.has(d.id)).length
            return (
              <CollapsibleGroup
                key={sem}
                title={`Семестр ${sem}`}
                meta={`${filled} / ${disciplines.length}`}
              >
                <ul className="flex flex-col">
                  {disciplines.map((d) => (
                    <GradeRow
                      key={d.id}
                      disciplineId={d.id}
                      disciplineName={d.name}
                      grade={gradeByDisciplineId.get(d.id) ?? null}
                      onChange={setGrade}
                    />
                  ))}
                </ul>
              </CollapsibleGroup>
            )
          })}
        </div>
      )}
    </div>
  )
}

interface GradeRowProps {
  disciplineId: string
  disciplineName: string
  grade: number | null
  onChange: (id: string, name: string, grade: number | null) => void
}

const GradeRow = memo(function GradeRow({
  disciplineId,
  disciplineName,
  grade,
  onChange,
}: GradeRowProps) {
  const value = grade === null ? NONE_VALUE : String(grade)
  return (
    <li className="flex items-center justify-between gap-[var(--space-base)] border-b border-[color:var(--color-border)] py-[var(--space-sm)] pl-[var(--space-lg)] last:border-b-0">
      <span className="text-[length:var(--text-base)] text-[color:var(--color-text)]">
        {disciplineName}
      </span>
      <Select
        value={value}
        onValueChange={(v) =>
          onChange(disciplineId, disciplineName, v === NONE_VALUE ? null : Number(v))
        }
      >
        <SelectTrigger size="sm" className="w-[112px] tabular-nums">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE_VALUE}>—</SelectItem>
          {GRADE_OPTIONS.map((g) => (
            <SelectItem key={g} value={String(g)}>
              {g}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </li>
  )
})

function GradesSkeleton() {
  return (
    <div className="flex flex-col gap-[var(--space-lg)]">
      {[3, 4].map((rows, i) => (
        <div key={i} className="flex flex-col gap-[var(--space-sm)]">
          <Skeleton className="h-3 w-24" />
          <div className="flex flex-col gap-[var(--space-sm)]">
            {Array.from({ length: rows }).map((_, j) => (
              <div key={j} className="flex items-center justify-between">
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-7 w-[112px]" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
