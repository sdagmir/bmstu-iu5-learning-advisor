/**
 * Типы API — ручные, синхронизированы с docs/API_REFERENCE.md.
 * Расширяются по мере подключения эндпоинтов в соответствующих фазах.
 */

// --- Перечисления (enums как string-union для erasableSyntaxOnly) ---

export type UserRole = 'student' | 'admin'

/** X1 — карьерная цель */
export type CareerGoal =
  | 'ml'
  | 'backend'
  | 'frontend'
  | 'cybersecurity'
  | 'system'
  | 'devops'
  | 'mobile'
  | 'gamedev'
  | 'qa'
  | 'analytics'
  | 'undecided'

/** X3 — статус Технопарка (none = не участвует) */
export type TechparkStatus = 'none' | 'backend' | 'frontend' | 'ml' | 'mobile'

/** X4 — предпочтение нагрузки */
export type WorkloadPref = 'light' | 'normal' | 'intensive'

// --- Auth ---

export interface LoginRequest {
  email: string
  password: string
}

/** Регистрация принимает только email + password (бэк сам создаёт профиль). */
export interface RegisterRequest {
  email: string
  password: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RefreshRequest {
  refresh_token: string
}

// --- Users ---

export interface UserMe {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  semester: number | null
  career_goal: CareerGoal | null
  technopark_status: TechparkStatus | null
  workload_pref: WorkloadPref | null
  created_at: string
}

/**
 * PATCH /users/me — частичный апдейт.
 * Любое поле опционально, передавать только изменившиеся.
 * `null` = очистить поле в БД.
 */
export interface ProfileUpdate {
  semester?: number | null
  career_goal?: CareerGoal | null
  technopark_status?: TechparkStatus | null
  workload_pref?: WorkloadPref | null
}

// --- Catalog ---

export type CKCourseCategory =
  | 'ml'
  | 'development'
  | 'security'
  | 'testing'
  | 'management'
  | 'other'

export interface Discipline {
  id: string
  name: string
  semester: number
  credits: number
  type: 'mandatory' | 'elective' | 'choice'
  control_form: string
  department: string
}

export interface CKCourse {
  id: string
  name: string
  description: string | null
  category: CKCourseCategory
  credits: number
}

// --- Grades & Completed CK ---

export interface GradeRead {
  discipline_id: string
  discipline_name: string
  grade: number
}

export interface GradePut {
  discipline_id: string
  grade: number
}

export interface CompletedCK {
  ck_course_id: string
  ck_course_name: string
  ck_course_category: CKCourseCategory
  completed_at: string
}

// --- Simulator (admin only) ---

export type CKDevStatus = 'yes' | 'no' | 'partial'
export type CoverageLevel = 'low' | 'medium' | 'high'
export type CKCategoryCount = 'few' | 'many'

/** StudentProfile для `POST /expert/evaluate`. Все поля X1–X12. */
export interface SimulatorProfile {
  user_id: string
  semester: number
  career_goal: CareerGoal
  technopark_status: TechparkStatus
  workload_pref: WorkloadPref
  completed_ck_ml: boolean
  ck_dev_status: CKDevStatus
  completed_ck_security: boolean
  completed_ck_testing: boolean
  weak_math: boolean
  weak_programming: boolean
  coverage: CoverageLevel
  ck_count_in_category: CKCategoryCount
}

export interface TraceEntry {
  rule: string
  name: string
  group: string
  fired: boolean
  skipped_reason: string | null
}

export interface EvaluateTrace {
  profile_snapshot: Record<string, unknown>
  total_checked: number
  total_fired: number
  fired_rule_ids: string[]
  entries: TraceEntry[]
}

export interface EvaluateDebugResponse {
  recommendations: Recommendation[]
  trace: EvaluateTrace
}

// --- Recommendations ---

export type RecommendationCategory =
  | 'ck_course'
  | 'technopark'
  | 'focus'
  | 'coursework'
  | 'warning'
  | 'strategy'

export type RecommendationPriority = 'high' | 'medium' | 'low'

/**
 * Y1–Y6 — выход ЭС. Совпадает с ответом `POST /expert/evaluate`.
 * `competency_gap` — UID компетенции, которую закрывает рекомендация (или null).
 */
export interface CKCourseLink {
  name: string
  description: string | null
  category: string
  credits: number
}

export interface Recommendation {
  rule_id: string
  category: RecommendationCategory
  title: string
  priority: RecommendationPriority
  reasoning: string
  competency_gap: string | null
  /** Для category=ck_course — детальная инфа курса из БД, если title совпал. */
  linked_course?: CKCourseLink | null
}

// --- Chat ---

export interface ChatHistoryItem {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  history: ChatHistoryItem[]
}

export interface ChatReplyDebug {
  rules_fired?: string[]
  rag_chunks?: string[]
  tool_calls?: Array<{ function: string; arguments: Record<string, unknown> }>
  profile_changes?: Record<string, unknown>
}

export interface ChatResponse {
  reply: string
  debug: ChatReplyDebug | null
}

// --- RAG (Phase 10) ---

export interface RagDocumentChunk {
  content: string
  source: string
  score: number
}

export interface RagSearchRequest {
  query: string
  top_k?: number
}

export interface RagDocumentUpload {
  source: string
  text: string
}

export interface RagDocumentUploadResult {
  source: string
  chunks_count: number
}

export interface RagStats {
  total_chunks: number
}

/** `GET /rag/documents` — агрегат по уникальному source. */
export interface RagDocumentSummary {
  source: string
  chunks_count: number
  indexed_at: string | null
}

// --- Coverage (студент, GET /users/me/coverage) ---

export interface CompetencyCoverageItem {
  competency_id: string
  name: string
  category: CompetencyCategory
  has: boolean
  needed: boolean
}

export interface CoverageResponse {
  items: CompetencyCoverageItem[]
  /** 0–100, % покрытия целевого профиля */
  coverage_percent: number
}

// --- История рекомендаций (студент, GET /expert/recommendations/history) ---

export interface RecommendationSnapshot {
  id: string
  created_at: string
  recommendations: Recommendation[]
  /** Человекочитаемая строка вида «Цель: backend → ml; Семестр: 4 → 5» */
  profile_change_summary: string | null
}

// --- LLM-трейсы (admin, GET /admin/traces) ---

export type TraceEndpoint = 'message' | 'message/debug'
export type TraceStatus = 'ok' | 'error' | 'timeout'

/** Запись в ленте `/admin/traces`. */
export interface TraceSummary {
  id: string
  created_at: string
  user_email: string
  endpoint: TraceEndpoint
  latency_ms: number
  status: TraceStatus
  rules_fired_count: number
  request_preview: string
}

/** Полная запись `/admin/traces/{id}`. */
export interface TraceDetail {
  id: string
  created_at: string
  user_id: string
  user_email: string
  endpoint: TraceEndpoint
  request_message: string
  response_text: string
  debug: ChatReplyDebug | null
  latency_ms: number
  status: TraceStatus
  model_name: string | null
}

// --- Admin: Каталог (Phase 9) ---

/** Категория компетенции (бэк: `CompetencyCategory`). */
export type CompetencyCategory =
  | 'programming'
  | 'math'
  | 'data'
  | 'ml'
  | 'engineering'
  | 'networks'
  | 'system'
  | 'applied'

/** Тип дисциплины. */
export type DisciplineType = 'mandatory' | 'elective' | 'choice'

export interface AdminCompetency {
  id: string
  tag: string
  name: string
  category: CompetencyCategory
}

export interface AdminCompetencyCreate {
  tag: string
  name: string
  category: CompetencyCategory
}

export interface AdminDiscipline {
  id: string
  name: string
  semester: number
  credits: number
  type: DisciplineType
  control_form: string
  department: string | null
  competencies: AdminCompetency[]
}

export interface AdminDisciplineCreate {
  name: string
  semester: number
  credits: number
  type: DisciplineType
  control_form: string
  department?: string | null
  competency_ids: string[]
}

export interface AdminCKCourse {
  id: string
  name: string
  description: string | null
  category: CKCourseCategory
  credits: number
  competencies: AdminCompetency[]
  prerequisites: AdminCompetency[]
}

export interface AdminCKCourseCreate {
  name: string
  description?: string | null
  category: CKCourseCategory
  credits?: number
  competency_ids: string[]
  prerequisite_ids: string[]
}

export interface AdminCareerDirection {
  id: string
  name: string
  description: string | null
  example_jobs: string | null
  competencies: AdminCompetency[]
}

export interface AdminCareerDirectionCreate {
  name: string
  description?: string | null
  example_jobs?: string | null
  competency_ids: string[]
}

export interface AdminFocusAdvice {
  id: string
  discipline_id: string
  career_direction_id: string
  focus_advice: string
  reasoning: string | null
}

export interface AdminFocusAdviceCreate {
  discipline_id: string
  career_direction_id: string
  focus_advice: string
  reasoning?: string | null
}

export interface AdminUser {
  id: string
  email: string
  role: UserRole
  is_active: boolean
  semester: number | null
  career_goal: CareerGoal | null
  technopark_status: TechparkStatus | null
  workload_pref: WorkloadPref | null
  created_at: string
}

export interface AdminUserUpdate {
  role?: UserRole | undefined
  is_active?: boolean | undefined
}

// --- Admin: Конструктор правил ЭС (Phase 7) ---

/** Группа правила — соответствует RuleGroup на бэке. */
export type RuleGroup =
  | 'ck_programs'
  | 'basic_universal'
  | 'technopark'
  | 'discipline_focus'
  | 'coursework'
  | 'warnings'
  | 'strategy'

/**
 * Правило ЭС — полное представление из `GET /admin/rules`.
 * `condition` и `recommendation` — свободные JSON-объекты,
 * валидируем структуру локально через zod.
 *
 * `trigger_count` — счётчик срабатываний в production-движке
 * (только при `GET /expert/my-recommendations`). Не растёт у
 * preview/sandbox/what-if вызовов.
 */
export interface Rule {
  id: string
  number: number
  group: RuleGroup
  name: string
  description: string
  condition: Record<string, unknown>
  recommendation: Record<string, unknown>
  priority: number
  is_active: boolean
  is_published: boolean
  trigger_count: number
}

/** POST /admin/rules — все обязательные поля. */
export interface RuleCreate {
  number: number
  group: RuleGroup
  name: string
  description?: string
  condition: Record<string, unknown>
  recommendation: Record<string, unknown>
  priority?: number
  is_active?: boolean
}

/** PATCH /admin/rules/{id} — только то что меняется. */
export interface RuleUpdate {
  group?: RuleGroup
  name?: string
  description?: string
  condition?: Record<string, unknown>
  recommendation?: Record<string, unknown>
  priority?: number
  is_active?: boolean
}

/** Состояние pessimistic-лока конструктора правил. */
export interface RuleEditingLockStatus {
  is_locked: boolean
  admin_id: string | null
  admin_email: string | null
  acquired_at: string | null
  expires_at: string | null
  owned_by_me: boolean
}

export interface RulePreviewRequest {
  profile: SimulatorProfile | Record<string, unknown>
  include_drafts?: boolean
}

export interface RulePreviewResponse {
  recommendations: Recommendation[]
  fired_rule_ids: string[]
  total_checked: number
  total_fired: number
}

// --- Ошибки ---

export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}

export interface ValidationErrorBody {
  detail: Array<{
    type: string
    loc: string[]
    msg: string
    input?: unknown
  }>
}
