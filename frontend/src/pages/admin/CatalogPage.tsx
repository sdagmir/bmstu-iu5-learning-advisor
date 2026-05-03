import { NavLink, Navigate, useParams } from 'react-router-dom'
import { Stack } from '@phosphor-icons/react'
import { PageTopBar } from '@/components/common/PageTopBar'
import { CrudTable } from '@/features/catalog/CrudTable'
import { competenciesConfig } from '@/features/catalog/entities/competencies'
import { disciplinesConfig } from '@/features/catalog/entities/disciplines'
import { ckCoursesConfig } from '@/features/catalog/entities/ck-courses'
import { careerDirectionsConfig } from '@/features/catalog/entities/career-directions'
import { focusAdvicesConfig } from '@/features/catalog/entities/focus-advices'
import { usersConfig } from '@/features/catalog/entities/users'
import { routes } from '@/constants/routes'
import { cn } from '@/lib/utils'

const CONFIGS = {
  competencies: competenciesConfig,
  disciplines: disciplinesConfig,
  'ck-courses': ckCoursesConfig,
  'career-directions': careerDirectionsConfig,
  'focus-advices': focusAdvicesConfig,
  users: usersConfig,
} as const

type EntityKey = keyof typeof CONFIGS

const ENTITY_ORDER: ReadonlyArray<EntityKey> = [
  'competencies',
  'disciplines',
  'ck-courses',
  'career-directions',
  'focus-advices',
  'users',
]

/**
 * Phase 9 — каталог. Все 6 сущностей рендерятся через generic CrudTable
 * по конфигу. Переключение сверху — sub-nav из 6 ссылок. URL `/admin/catalog/:entity`.
 *
 * `users` едет тем же конфигом, но без create/delete (только PATCH role/is_active).
 */
export default function CatalogPage() {
  const { entity = '' } = useParams<{ entity: string }>()

  if (!isEntityKey(entity)) {
    return <Navigate to={routes.admin.catalog('competencies')} replace />
  }

  const config = CONFIGS[entity]

  return (
    <>
      <PageTopBar title="Каталог" icon={<Stack size={18} weight="regular" />} />

      <nav className="sticky top-[58px] z-10 flex items-center gap-[var(--space-xs)] overflow-x-auto border-b border-[color:var(--color-border)] bg-[color:var(--color-bg)] px-[var(--space-2xl)] py-[var(--space-sm)]">
        {ENTITY_ORDER.map((key) => (
          <NavLink
            key={key}
            to={routes.admin.catalog(key)}
            end
            className={({ isActive }) =>
              cn(
                'shrink-0 rounded-[6px] px-[var(--space-md)] py-[var(--space-xs)] text-[length:var(--text-sm)] transition-colors',
                isActive
                  ? 'bg-[color:var(--color-primary-soft)] font-medium text-[color:var(--color-primary)]'
                  : 'text-[color:var(--color-text-muted)] hover:bg-[color:var(--color-surface-hover)] hover:text-[color:var(--color-text)]',
              )
            }
          >
            {CONFIGS[key].pluralName}
          </NavLink>
        ))}
      </nav>

      <CrudTable config={config} />
    </>
  )
}

function isEntityKey(s: string): s is EntityKey {
  return s in CONFIGS
}
