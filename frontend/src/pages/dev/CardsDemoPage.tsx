import { Stack } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { PageHeader } from '@/components/common/PageHeader'
import { RecommendationCard } from '@/features/recommendation/RecommendationCard'
import type { Recommendation } from '@/types/api'

/** Демо-страница для калибровки RecommendationCard. Удалить перед защитой. */

const SAMPLES: Recommendation[] = [
  {
    rule_id: 'R-017',
    category: 'ck_course',
    title: 'Курс ЦК «Инженер машинного обучения»',
    priority: 'high',
    reasoning:
      'Карьерная цель — ML, базовый трек по разработке пройден на 4+. Программа закрывает ключевой gap в нейросетях и MLOps.',
    competency_gap: 'ml_basics',
  },
  {
    rule_id: 'R-024',
    category: 'technopark',
    title: 'ML-трек Технопарка',
    priority: 'medium',
    reasoning: 'Оптимальный трек для целевого профиля ML. Подходит при средней нагрузке.',
    competency_gap: null,
  },
  {
    rule_id: 'R-038',
    category: 'focus',
    title: 'Упор на нейросети в курсовой по «Системам ИИ»',
    priority: 'medium',
    reasoning:
      'Тема курсовой пересекается с целевым профилем; сделать акцент на CNN/трансформерах усилит портфолио.',
    competency_gap: 'neural_nets',
  },
  {
    rule_id: 'R-042',
    category: 'coursework',
    title: 'Тема курсовой: «Сегментация медицинских изображений»',
    priority: 'low',
    reasoning:
      'Подходящая тема при цели ML и интересе к CV. Опционально, есть и другие подходящие темы.',
    competency_gap: 'cv',
  },
  {
    rule_id: 'R-049',
    category: 'warning',
    title: 'Слабая база по дискретной математике',
    priority: 'high',
    reasoning:
      'Средняя оценка по дискретной математике ниже 4.0 — это базовый предмет для всех целевых профилей кроме «Аналитика».',
    competency_gap: 'discrete_math',
  },
  {
    rule_id: 'R-051',
    category: 'strategy',
    title: 'Сейчас фокус на профильной математике, в 6-м семестре — на ЦК',
    priority: 'medium',
    reasoning:
      'Текущий семестр — 5-й, плотный по обязательным предметам. Подтянуть базы математики, ЦК-программу удобно начать в 6-м семестре.',
    competency_gap: null,
  },
]

const RELATED_COMPETENCIES = [
  { id: 'ml-basics', name: 'Основы ML' },
  { id: 'python', name: 'Python для DS' },
  { id: 'linear-algebra', name: 'Линейная алгебра' },
  { id: 'stats', name: 'Статистика' },
]

export default function CardsDemoPage() {
  return (
    <>
      <PageTopBar title="RecommendationCard demo" icon={<Stack size={18} weight="regular" />} />
      <div className="px-[var(--space-2xl)] py-[var(--space-2xl)]">
        <PageHeader
          title="RecommendationCard"
          description="Hero-компонент продукта. Все 6 категорий, 3 приоритета, оба режима. Удалить перед защитой."
        />

        <div className="flex max-w-[720px] flex-col gap-[var(--space-3xl)]">
          <DemoSection title="User mode · все категории">
            {SAMPLES.map((s) => (
              <RecommendationCard key={s.rule_id} recommendation={s} />
            ))}
          </DemoSection>

          <DemoSection
            title="User mode · expanded"
            description="С связанными компетенциями chips в раскрытой секции."
          >
            <RecommendationCard
              recommendation={SAMPLES[0]!}
              relatedCompetencies={RELATED_COMPETENCIES}
            />
          </DemoSection>

          <DemoSection
            title="Admin mode"
            description="rule_id справа моноспейсом + счётчик срабатываний в meta-tail."
          >
            {SAMPLES.slice(0, 3).map((s, i) => (
              <RecommendationCard
                key={s.rule_id}
                recommendation={s}
                mode="admin"
                triggerCount={142 - i * 30}
                onRuleClick={(id) => console.log('open rule', id)}
                {...(i === 0 ? { relatedCompetencies: RELATED_COMPETENCIES } : {})}
              />
            ))}
          </DemoSection>
        </div>
      </div>
    </>
  )
}

function DemoSection({
  title,
  description,
  children,
}: {
  title: string
  description?: string
  children: React.ReactNode
}) {
  return (
    <section className="flex flex-col gap-[var(--space-base)]">
      <div className="flex flex-col gap-[var(--space-xs)] border-b border-[color:var(--color-border)] pb-[var(--space-sm)]">
        <h2 className="font-serif text-[length:var(--text-xl)] font-semibold tracking-tight text-[color:var(--color-text)]">
          {title}
        </h2>
        {description && (
          <p className="text-[length:var(--text-sm)] text-[color:var(--color-text-muted)]">
            {description}
          </p>
        )}
      </div>
      <div className="flex flex-col">{children}</div>
    </section>
  )
}
