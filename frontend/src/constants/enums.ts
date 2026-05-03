import type {
  CareerGoal,
  CKCourseCategory,
  CompetencyCategory,
  DisciplineType,
  RecommendationCategory,
  RecommendationPriority,
  RuleGroup,
  TechparkStatus,
  UserRole,
  WorkloadPref,
} from '@/types/api'

/**
 * Русские подписи enum'ов профиля. Любой enum-визуал в UI берёт текст отсюда —
 * чтобы не плодить повторов. Описания (если есть) — короткие пояснения для radio.
 */

export const ALL_CAREER_GOALS: readonly CareerGoal[] = [
  'ml',
  'backend',
  'frontend',
  'cybersecurity',
  'system',
  'devops',
  'mobile',
  'gamedev',
  'qa',
  'analytics',
  'undecided',
] as const

export const CAREER_GOAL_LABELS: Record<CareerGoal, string> = {
  ml: 'Machine Learning',
  backend: 'Backend-разработка',
  frontend: 'Frontend-разработка',
  cybersecurity: 'Кибербезопасность',
  system: 'Системное программирование',
  devops: 'DevOps',
  mobile: 'Мобильная разработка',
  gamedev: 'Разработка игр',
  qa: 'Тестирование',
  analytics: 'Аналитика данных',
  undecided: 'Ещё не определился',
}

export const ALL_TECHPARK_STATUSES: readonly TechparkStatus[] = [
  'none',
  'backend',
  'frontend',
  'ml',
  'mobile',
] as const

export const TECHPARK_STATUS_LABELS: Record<TechparkStatus, string> = {
  none: 'Не участвую',
  backend: 'Backend-трек',
  frontend: 'Frontend-трек',
  ml: 'ML-трек',
  mobile: 'Mobile-трек',
}

export const TECHPARK_STATUS_DESCRIPTIONS: Record<TechparkStatus, string> = {
  none: 'Пока не записан в Технопарк',
  backend: 'Серверная разработка, базы, инфра',
  frontend: 'Клиентская веб-разработка',
  ml: 'Машинное обучение, нейросети',
  mobile: 'iOS / Android-разработка',
}

export const ALL_WORKLOAD_PREFS: readonly WorkloadPref[] = ['light', 'normal', 'intensive'] as const

export const WORKLOAD_PREF_LABELS: Record<WorkloadPref, string> = {
  light: 'Лёгкая',
  normal: 'Обычная',
  intensive: 'Интенсивная',
}

export const WORKLOAD_PREF_DESCRIPTIONS: Record<WorkloadPref, string> = {
  light: 'Только обязательные дисциплины',
  normal: 'Учебный план + 1–2 факультатива',
  intensive: 'Максимум: ЦК, Технопарк, факультативы',
}

// --- Recommendation labels ---

export const RECOMMENDATION_CATEGORY_LABELS: Record<RecommendationCategory, string> = {
  ck_course: 'Курс ЦК',
  technopark: 'Технопарк',
  focus: 'Фокус в дисциплине',
  coursework: 'Тема курсовой',
  warning: 'Предупреждение',
  strategy: 'Стратегия',
}

/** Тон копи: «Курс ЦК · важно», «Фокус в дисциплине · рекомендуется» (per design-brief). */
export const RECOMMENDATION_PRIORITY_LABELS: Record<RecommendationPriority, string> = {
  high: 'важно',
  medium: 'рекомендуется',
  low: 'по желанию',
}

// --- Admin: группы правил ЭС (Phase 7) ---

export const ALL_RULE_GROUPS: readonly RuleGroup[] = [
  'ck_programs',
  'basic_universal',
  'technopark',
  'discipline_focus',
  'coursework',
  'warnings',
  'strategy',
] as const

export const RULE_GROUP_LABELS: Record<RuleGroup, string> = {
  ck_programs: 'Программы ЦК',
  basic_universal: 'Базовые универсальные',
  technopark: 'Технопарк',
  discipline_focus: 'Фокус в дисциплине',
  coursework: 'Курсовая',
  warnings: 'Предупреждения',
  strategy: 'Стратегия',
}

// --- Admin: каталог (Phase 9) ---

export const ALL_COMPETENCY_CATEGORIES: readonly CompetencyCategory[] = [
  'programming',
  'math',
  'data',
  'ml',
  'engineering',
  'networks',
  'system',
  'applied',
] as const

export const COMPETENCY_CATEGORY_LABELS: Record<CompetencyCategory, string> = {
  programming: 'Программирование',
  math: 'Математика',
  data: 'Данные',
  ml: 'Machine Learning',
  engineering: 'Инженерия ПО',
  networks: 'Сети',
  system: 'Системное',
  applied: 'Прикладные',
}

export const ALL_DISCIPLINE_TYPES: readonly DisciplineType[] = [
  'mandatory',
  'elective',
  'choice',
] as const

export const DISCIPLINE_TYPE_LABELS: Record<DisciplineType, string> = {
  mandatory: 'Обязательная',
  elective: 'Факультатив',
  choice: 'По выбору',
}

export const ALL_USER_ROLES: readonly UserRole[] = ['student', 'admin'] as const

export const USER_ROLE_LABELS: Record<UserRole, string> = {
  student: 'Студент',
  admin: 'Администратор',
}

// --- CK course categories ---

export const CK_CATEGORY_LABELS: Record<CKCourseCategory, string> = {
  ml: 'Machine Learning',
  development: 'Разработка',
  security: 'Безопасность',
  testing: 'Тестирование',
  management: 'Управление',
  other: 'Другое',
}
