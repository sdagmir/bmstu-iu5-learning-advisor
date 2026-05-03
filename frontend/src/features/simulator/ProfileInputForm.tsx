import { useId } from 'react'
import { Switch } from '@/components/ui/switch'
import { CareerGoalSection } from '@/features/profile/sections/CareerGoalSection'
import { SemesterSection } from '@/features/profile/sections/SemesterSection'
import { TechnoparkSection } from '@/features/profile/sections/TechnoparkSection'
import { WorkloadSection } from '@/features/profile/sections/WorkloadSection'
import { cn } from '@/lib/utils'
import type {
  CKCategoryCount,
  CKDevStatus,
  CoverageLevel,
  SimulatorProfile,
} from '@/types/api'

interface ProfileInputFormProps {
  profile: SimulatorProfile
  onChange: (patch: Partial<SimulatorProfile>) => void
}

const CK_DEV_OPTIONS: Array<{ value: CKDevStatus; label: string }> = [
  { value: 'no', label: 'Нет' },
  { value: 'partial', label: 'Частично' },
  { value: 'yes', label: 'Да' },
]

const COVERAGE_OPTIONS: Array<{ value: CoverageLevel; label: string }> = [
  { value: 'low', label: 'Низкое' },
  { value: 'medium', label: 'Среднее' },
  { value: 'high', label: 'Высокое' },
]

const CK_COUNT_OPTIONS: Array<{ value: CKCategoryCount; label: string }> = [
  { value: 'few', label: '0–2' },
  { value: 'many', label: '3+' },
]

/**
 * Форма X1–X12 для Simulator (Phase 8) и Sandbox (Phase 7). Должна работать
 * в узких колонках от ~280px и при этом ОСТАВАТЬСЯ ЧИТАЕМОЙ.
 *
 * Иерархия 3 уровня (см. Linear / Stripe / Apple Settings — там же копал):
 *   1. Заголовок секции — `text-sm font-semibold` + видимая граница сверху
 *   2. Метка поля (свитч / segmented) — `text-sm` основной цвет
 *   3. Сабтекст / опция в pill — `text-xs text-muted`
 *
 * Видимая `border-t` между секциями важнее «пустого gap'а» — в плотной форме
 * пробел читается как «продолжение списка», линия — как «новый раздел».
 *
 * `useId()` уникальные id, чтобы при двойном монтировании в одной сессии
 * htmlFor не вёл на чужой контрол.
 */
export function ProfileInputForm({ profile, onChange }: ProfileInputFormProps) {
  const formId = useId()

  return (
    <div className="flex min-w-0 flex-col divide-y divide-[color:var(--color-border)]">
      <Slot>
        <CareerGoalSection
          value={profile.career_goal}
          onChange={(v) => onChange({ career_goal: v })}
        />
      </Slot>
      <Slot>
        <SemesterSection value={profile.semester} onChange={(v) => onChange({ semester: v })} />
      </Slot>
      <Slot>
        <TechnoparkSection
          value={profile.technopark_status}
          onChange={(v) => onChange({ technopark_status: v })}
        />
      </Slot>
      <Slot>
        <WorkloadSection
          value={profile.workload_pref}
          onChange={(v) => onChange({ workload_pref: v })}
        />
      </Slot>

      <Section title="Пройденные ЦК">
        <SwitchRow
          formId={formId}
          name="ml"
          label="ML"
          checked={profile.completed_ck_ml}
          onCheckedChange={(v) => onChange({ completed_ck_ml: v })}
        />
        <SwitchRow
          formId={formId}
          name="security"
          label="Безопасность"
          checked={profile.completed_ck_security}
          onCheckedChange={(v) => onChange({ completed_ck_security: v })}
        />
        <SwitchRow
          formId={formId}
          name="testing"
          label="Тестирование"
          checked={profile.completed_ck_testing}
          onCheckedChange={(v) => onChange({ completed_ck_testing: v })}
        />
        <SegmentedRow<CKDevStatus>
          label="Разработка"
          value={profile.ck_dev_status}
          options={CK_DEV_OPTIONS}
          onChange={(v) => onChange({ ck_dev_status: v })}
        />
      </Section>

      <Section title="Слабая база">
        <SwitchRow
          formId={formId}
          name="weak-math"
          label="Математика"
          checked={profile.weak_math}
          onCheckedChange={(v) => onChange({ weak_math: v })}
        />
        <SwitchRow
          formId={formId}
          name="weak-prog"
          label="Программирование"
          checked={profile.weak_programming}
          onCheckedChange={(v) => onChange({ weak_programming: v })}
        />
      </Section>

      <Section title="Производные">
        <SegmentedRow<CoverageLevel>
          label="Покрытие профиля"
          value={profile.coverage}
          options={COVERAGE_OPTIONS}
          onChange={(v) => onChange({ coverage: v })}
        />
        <SegmentedRow<CKCategoryCount>
          label="Курсов в категории"
          value={profile.ck_count_in_category}
          options={CK_COUNT_OPTIONS}
          onChange={(v) => onChange({ ck_count_in_category: v })}
        />
      </Section>
    </div>
  )
}

/**
 * Слот без заголовка — для X1–X4 у которых есть свой <Label>. Просто даёт
 * вертикальный ритм + участвует в `divide-y`.
 */
function Slot({ children }: { children: React.ReactNode }) {
  return <div className="min-w-0 py-[var(--space-lg)] first:pt-0">{children}</div>
}

/** Заголовок + содержимое. Заголовок полужирный — psychological anchor. */
function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="flex min-w-0 flex-col gap-[var(--space-md)] py-[var(--space-lg)]">
      <h3 className="text-[length:var(--text-sm)] font-semibold text-[color:var(--color-text)]">
        {title}
      </h3>
      <div className="flex min-w-0 flex-col gap-[var(--space-xs)]">{children}</div>
    </section>
  )
}

interface SwitchRowProps {
  formId: string
  name: string
  label: string
  checked: boolean
  onCheckedChange: (v: boolean) => void
}

/**
 * Строка свитча. Лейбл слева (truncate), Switch справа фикс-ширины (32px) —
 * всегда виден. Контраст unchecked-состояния и translate-x бегунка теперь
 * вшиты в сам компонент Switch (см. components/ui/switch.tsx).
 */
function SwitchRow({ formId, name, label, checked, onCheckedChange }: SwitchRowProps) {
  const id = `${formId}-${name}`
  return (
    <label
      htmlFor={id}
      className="group flex cursor-pointer items-center gap-[var(--space-base)] rounded-[6px] py-[var(--space-xs)] text-[length:var(--text-sm)] text-[color:var(--color-text)] hover:text-[color:var(--color-primary)]"
    >
      <span className="min-w-0 flex-1 truncate">{label}</span>
      <Switch
        id={id}
        checked={checked}
        onCheckedChange={onCheckedChange}
        className="shrink-0"
      />
    </label>
  )
}

interface SegmentedRowProps<T extends string> {
  label: string
  value: T
  options: Array<{ value: T; label: string }>
  onChange: (v: T) => void
}

/**
 * Segmented control. Лейбл сверху мелким муть-цветом (визуально подчинён
 * заголовку секции), пилюли снизу равной ширины через grid-template-cols.
 *
 * Selected: бордер + бэкграунд primary-soft + bold weight + primary-цвет
 * текста — четыре сигнала разом, чтобы выбор было не пропустить периферийным
 * зрением. На surface-muted-фоне sandbox'а добавляем `bg-surface` для
 * unselected, иначе пилюли не отделяются от фона панели.
 */
function SegmentedRow<T extends string>({
  label,
  value,
  options,
  onChange,
}: SegmentedRowProps<T>) {
  return (
    <div className="flex flex-col gap-[var(--space-xs)] py-[var(--space-xs)]">
      <span className="text-[length:var(--text-xs)] text-[color:var(--color-text-muted)]">
        {label}
      </span>
      <div
        role="radiogroup"
        aria-label={label}
        className="grid w-full gap-[var(--space-xs)]"
        style={{ gridTemplateColumns: `repeat(${options.length}, minmax(0, 1fr))` }}
      >
        {options.map((o) => {
          const selected = o.value === value
          return (
            <button
              key={o.value}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => onChange(o.value)}
              className={cn(
                'flex h-9 min-w-0 items-center justify-center rounded-[6px] border px-[var(--space-sm)] text-[length:var(--text-sm)] transition-colors',
                selected
                  ? 'border-[color:var(--color-primary)] bg-[color:var(--color-primary-soft)] font-semibold text-[color:var(--color-primary)]'
                  : 'border-[color:var(--color-border)] bg-[color:var(--color-surface)] text-[color:var(--color-text-muted)] hover:border-[color:var(--color-border-strong)] hover:text-[color:var(--color-text)]',
              )}
            >
              <span className="truncate">{o.label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
