/** API types — mirror of backend Pydantic schemas (phase 1). */

export interface StudentProfile {
  id: string
  user_id: string
  grade: string | null
  track: string | null
  target: string | null
}

export interface AuthUser {
  id: string
  email: string
  full_name: string | null
  role: 'student' | 'advisor' | 'parent' | 'admin'
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
  student: StudentProfile | null
}

export interface MeResponse {
  user: AuthUser
  student: StudentProfile | null
}

export interface CheckinDims {
  energy: number
  focus: number
  motivation: number
  stress: number
  fatigue: number
}

export interface CheckinOut extends CheckinDims {
  date: string
  date_jalali: string
  updated_at: string
}

export interface StateOut {
  today: CheckinOut | null
  last: CheckinOut | null
  data_days: number
}

export interface TaughtTopicOut {
  topic_id: string
  taught: boolean
  updated_at: string
}

// --- Phase 2: Books & Import (doc 09 §9.1) -----------------------------------

export type BlockType = 'topic' | 'mixed' | 'chapter_exam' | 'checkup' | 'konkur' | 'other'

export interface ResourceCounts {
  chapters: number
  topics: number
  questions: number
}

export interface BookResource {
  id: string
  title: string
  publisher: string
  subject: string | null
  counts: ResourceCounts
  created_at: string
}

export interface TreeNode {
  id: string
  title: string
  block_type: BlockType
  block_type_fa: string
  is_structural: boolean
  question_count: number
  taught: boolean
  /** doc 08 §8.8 — parent می‌تواند indeterminate باشد */
  taught_state: 'all' | 'none' | 'partial'
  children: TreeNode[]
}

export interface TreeOut {
  resource: BookResource
  tree: TreeNode[]
}

export interface ImportResult {
  resource: BookResource
  replaced: boolean
}

export interface ImportSchema {
  description: string
  toc_only: boolean
  rules: string[]
  fields: Record<string, { type: string; required: boolean; description?: string }>
  topic_fields: Record<string, { type: string; required: boolean; enum?: string[]; description?: string }>
  block_types: { value: BlockType; label_fa: string }[]
  block_type_inference: string[]
  example: Record<string, unknown>
  example_with_questions: Record<string, unknown>
}

// --- Phase 3: Test Engine (doc 08 §8.1-8.2, doc 09 §9.2-9.4) --------------------

export type SessionMode = 'timed' | 'untimed' | 'past'
export type Parity = 'any' | 'odd' | 'even'
export type AttemptStatus = 'answered' | 'unanswered' | 'not_entered'
export type AttemptResult = 'correct' | 'wrong' | 'blank' | 'unknown'
export type ErrorType = 'careless' | 'concept' | 'method' | 'memory' | 'other'

export interface TestSessionOut {
  id: string
  mode: SessionMode
  label: string | null
  resource_id: string | null
  resource_title: string | null
  source: string
  filters: Record<string, unknown>
  total_count: number
  planned_duration: number | null
  actual_duration: number | null
  penalty_k: number | null
  correct_count: number
  wrong_count: number
  unanswered_count: number
  not_entered_count: number
  percent_konkur: number | null
  percent_no_penalty: number | null
  started_at: string
  finished_at: string | null
  finished: boolean
}

export interface SessionQuestion {
  question_id: string | null
  number: number | null
  topic_id: string | null
  topic_title: string | null
  block_type: BlockType | null
  difficulty: number | null
  status: AttemptStatus | null
  result: AttemptResult | null
  answer: string | null
  correct_answer: string | null
  duration_seconds: number | null
}

export interface AttemptOut {
  id: string
  question_id: string | null
  topic_id: string | null
  question_number: number | null
  topic_title: string | null
  status: AttemptStatus
  result: AttemptResult
  answer: string | null
  correct_answer: string | null
  answer_key_version: number | null
  duration_seconds: number | null
  solved_at: string
}

export interface TopicAggregate {
  topic_id: string | null
  topic_title: string | null
  attempts: number
  duration_seconds: number
  correct: number
  wrong: number
  avg_seconds: number
}

export interface ScoringOut {
  total_count: number
  correct_count: number
  wrong_count: number
  unanswered_count: number
  not_entered_count: number
  percent_konkur: number | null
  percent_no_penalty: number | null
  penalty_k: number
}

export interface SessionCreateOut {
  session: TestSessionOut
  questions: SessionQuestion[]
}

export interface RecordsOut {
  added: number
  progress: ScoringOut
}

export interface FinishOut {
  session: TestSessionOut
  idempotent: boolean
  topics: TopicAggregate[]
}

export interface SessionDetailOut {
  session: TestSessionOut
  questions: SessionQuestion[]
  attempts: AttemptOut[]
  topics: TopicAggregate[]
}

export interface PreviewOut {
  resource_id: string
  resource_title: string
  available_in_scope: number
  matching: number
  numbers: number[]
  filters: Record<string, unknown>
  message: string | null
}

export interface PastImportOut {
  session: TestSessionOut
  created_session: boolean
  imported: number
  updated: number
  created_questions: number
  created_answer_keys: number
}

export interface ErrorNoteOut {
  id: string
  session_id: string | null
  question_id: string | null
  book_title: string | null
  topic_title: string | null
  question_number: number | null
  your_answer: string | null
  correct_answer: string | null
  error_type: ErrorType | null
  error_type_fa: string | null
  note: string | null
  created_at: string
}

// --- Phase 4 — Review & Learning & Settings (doc 10، doc 06) -------------------

export interface AppSettings {
  review_intervals: number[]
  include_blank_in_review: boolean
  max_daily_review: number
  min_cluster: number
  konkurs_penalty_k: number
  streak_grace_days: number
}

export interface ReviewMarks {
  review: boolean
  important: boolean
  hard: boolean
}

export interface MarksOut extends ReviewMarks {
  question_id: string
  updated_at: string | null
}

export type ReviewSource = 'wrong' | 'blank' | 'mark_review' | 'mark_important' | 'mark_hard'

export interface ReviewItemOut {
  id: string
  question_id: string
  number: number | null
  topic_id: string | null
  topic_title: string | null
  book_title: string | null
  source: ReviewSource
  source_fa: string
  status: 'pending' | 'scheduled' | 'absorbed'
  critical: boolean
  wrong_count: number
  review_count: number
  cycle_index: number
  cycle_length: number
  next_interval_days: number | null
  scheduled_date: string | null
  scheduled_date_jalali: string | null
  overdue_days: number
  your_answer: string | null
  correct_answer: string | null
  marks: ReviewMarks
}

export interface ReviewQueueOut {
  items: ReviewItemOut[]
  due_count: number
  upcoming_count: number
  absorbed_count: number
  intervals: number[]
  today_jalali: string
}

export interface RebuildOut {
  added: number
  updated: number
  reopened: number
  active: number
  learning_states: number
  intervals: number[]
}

export interface ClusterOut {
  topic_id: string | null
  topic_title: string
  book_title: string | null
  size: number
  critical_count: number
  suggested_count: number
}

export interface ClusterSuggestionOut {
  suggested: ReviewItemOut[]
  suggested_count: number
  clusters: ClusterOut[]
  due_count: number
  budget: number
  min_cluster: number
}

export interface LearningStateOut {
  id: string
  topic_id: string
  topic_title: string
  book_title: string | null
  coverage: number
  accuracy: number
  retention_est: number
  recency_score: number
  repeated_error_score: number
  exam_readiness: number
  confidence: number
  weakness: boolean
  total_questions: number
  attempted_questions: number
  correct_count: number
  wrong_count: number
  updated_at: string
}

export interface LearningStatesOut {
  items: LearningStateOut[]
}

// --- Phase 5 — Planning & Capacity & Today Hub (doc 11، doc 07.6، doc 06) -------

export type PlanTaskKind = 'study' | 'test' | 'review' | 'goal'
export type PlanTaskSource = 'generated' | 'manual' | 'recovered'
export type PlanTaskStatus = 'pending' | 'done' | 'skipped'
export type TimeBlockKind = 'school' | 'class' | 'free'
export type GoalKind = 'long' | 'month' | 'week'

export interface GoalOut {
  id: string
  title: string
  kind: GoalKind
  target_date: string | null
  target_date_jalali: string | null
  created_at: string | null
}

export interface GoalsOut {
  items: GoalOut[]
}

export interface CapacityOut {
  date: string
  date_jalali: string
  weekday_fa: string
  school_minutes: number
  class_minutes: number
  free_minutes: number
  has_blocks: boolean
  available_minutes: number
  suggested_task_count: number
  suggested_session_count: number
  completion_rate: number
  state_factor: number
  source: 'computed' | 'override'
}

export interface TimeBlockOut {
  id: string
  date: string
  kind: TimeBlockKind
  start: string
  end: string
  start_minutes: number
  end_minutes: number
  minutes: number
  title: string | null
  source: string
}

export interface TimeBlocksOut {
  date: string
  date_jalali: string
  blocks: TimeBlockOut[]
  capacity: CapacityOut
}

export interface PlanTaskOut {
  id: string
  date: string
  date_jalali: string
  kind: PlanTaskKind
  kind_fa: string
  title: string
  topic_id: string | null
  topic_title: string | null
  book_title: string | null
  minutes: number
  count: number | null
  status: PlanTaskStatus
  locked: boolean
  source: PlanTaskSource
  source_fa: string
  reason_code: string | null
  reason_fa: string | null
  order_index: number
}

export interface PlanDayCounts {
  total: number
  done: number
  locked: number
  minutes: number
}

export interface PlanDayOut {
  date: string
  date_jalali: string
  weekday_fa: string
  capacity: CapacityOut
  tasks: PlanTaskOut[]
  counts: PlanDayCounts
}

export interface WeekDaySummary {
  date: string
  date_jalali: string
  weekday_fa: string
  available_minutes: number
  suggested_task_count: number
  capacity_source: 'computed' | 'override'
  tasks_count: number
  minutes: number
}

export interface PipelineStep {
  step: string
  ms: number
  info: Record<string, unknown>
}

export interface PriorityItem {
  topic_id: string
  topic_title: string
  book_title: string | null
  score: number
  reason_codes: string[]
  review_due: number
  exam_readiness: number
  weakness: boolean
}

export interface GenerateWeekOut {
  week_start: string
  week_start_jalali: string
  days: WeekDaySummary[]
  created: number
  removed: number
  kept_locked: number
  priority: PriorityItem[]
  steps: PipelineStep[]
  run_id: string
  total_ms: number
}

export interface PriorityWeekOut {
  week_start: string
  week_start_jalali: string
  items: PriorityItem[]
  from_snapshot: boolean
  message: string | null
}

export interface RecoveryOut {
  moved: number
  days: Record<string, number>
  cap_per_day: number
  week_start: string
  tomorrow_share: number
}

export interface RecReason {
  code: string
  fa: string
}

export interface RecommendationPayload {
  kind: 'task' | 'review' | 'study' | 'test_easy' | 'none'
  title: string
  minutes?: number | null
  task_id?: string | null
  review_item_id?: string | null
  topic_id?: string | null
  /** «چرا این پیشنهاد؟» — توضیح فارسی با عدد و شاهد (doc 07 §7.6 #6، فاز ۷) */
  explain_fa?: string | null
}

export interface RecommendationOut {
  id: string
  date: string
  date_jalali: string
  status: 'suggested' | 'accepted' | 'rejected' | 'edited'
  payload: RecommendationPayload
  reasons: RecReason[]
}

export interface SparklineDay {
  date: string
  date_jalali: string
  weekday_fa: string
  done_minutes: number
  done_tasks: number
  planned_tasks: number
  attempts: number
  is_today: boolean
}

export interface TodayWeekDay {
  date: string
  date_jalali: string
  weekday_fa: string
  is_today: boolean
  tasks_count: number
  done_count: number
  locked_count: number
}

export interface TodayOut {
  date: string
  date_jalali: string
  weekday_fa: string
  greeting: string
  checkin: StateOut
  capacity: CapacityOut
  plan_items: PlanTaskOut[]
  plan_counts: { total: number; done: number; locked: number }
  review_top: ReviewItemOut[]
  review_due_count: number
  upcoming_exams: UpcomingExam[]
  recommendation: RecommendationOut | null
  week_sparkline: SparklineDay[]
  week: { week_start: string; week_start_jalali: string; days: TodayWeekDay[] }
}

export interface SplitOut {
  parts: number
  tasks: PlanTaskOut[]
}

/** ورودی PUT /plans/{date} — لیست جایگزین کل کارهای روز می‌شود (doc 11.4). */
export interface PlanTaskIn {
  id?: string
  title?: string
  kind?: PlanTaskKind
  minutes?: number
  count?: number
  status?: PlanTaskStatus
  locked?: boolean
  topic_id?: string
  reason_code?: string
}

export interface TimeBlockIn {
  kind: TimeBlockKind
  start: string | number
  end: string | number
  title?: string
}

// ---------------------------------------------------------------------------
// Phase 6 — Exam Center · Analytics · Reports · Export (doc 12, doc 08 §8.1)
// V2-A01: coverage / accuracy / volume همیشه سه بلوک جدا — هرگز یک عدد قاطی.
// ---------------------------------------------------------------------------

export type ExamKind = 'mock' | 'school_subject' | 'free'
export type ExamStatus = 'planned' | 'in_progress' | 'finished' | 'cancelled'

export interface ExamScoring {
  total_count: number
  correct_count: number
  wrong_count: number
  unanswered_count: number
  not_entered_count: number
  actual_duration_seconds: number | null
  penalty_k: number
  percent_konkur: number | null
  percent_no_penalty: number | null
}

export interface ExamOut {
  id: string
  kind: ExamKind
  kind_fa: string
  status: ExamStatus
  status_fa: string
  title: string
  note: string | null
  resource_id: string | null
  resource_title: string | null
  scheduled_date: string | null
  scheduled_date_jalali: string | null
  planned_duration_minutes: number | null
  subjects: string[]
  planned_topic_ids: string[]
  actual_topic_ids: string[]
  session_ids: string[]
  actual_duration_seconds: number | null
  duration_fa: string | null
  started_at: string | null
  finished_at: string | null
  scoring: ExamScoring | null
  created_at: string | null
}

export interface ExamListOut {
  items: ExamOut[]
  upcoming_count: number
}

export interface ExamSessionRow {
  id: string
  label: string | null
  resource_title: string | null
  finished?: boolean
  total_count: number | null
  correct_count: number | null
  wrong_count: number | null
  unanswered_count?: number
  not_entered_count?: number
  percent_konkur: number | null
  percent_no_penalty: number | null
  actual_duration?: number | null
}

export interface ExamTopicRow {
  topic_id: string
  topic_title: string | null
  book_title?: string | null
}

export interface ExamResultBody {
  scoring: ExamScoring
  sessions: ExamSessionRow[]
  actual_topics: ExamTopicRow[]
  planned_topics: ExamTopicRow[]
  duration_fa: string | null
  is_mock: boolean
}

export interface ExamResultOut extends ExamOut {
  result: ExamResultBody
}

/** Today Hub item 5 — آزمون نزدیک (doc 07 §7.6) */
export interface UpcomingExam {
  id: string
  title: string
  kind: ExamKind
  kind_fa: string
  status: ExamStatus
  status_fa: string
  scheduled_date: string | null
  scheduled_date_jalali: string | null
  days_until: number
  subjects: string[]
}

export interface ExamCreateIn {
  title: string
  kind?: ExamKind
  note?: string | null
  resource_id?: string | null
  scheduled_date?: string | null
  planned_duration_minutes?: number | null
  subjects?: string[]
  planned_topic_ids?: string[]
}

export interface ExamUpdateIn {
  title?: string
  note?: string | null
  scheduled_date?: string | null
  planned_duration_minutes?: number | null
  subjects?: string[]
  planned_topic_ids?: string[]
  status?: ExamStatus
}

export interface ExamSubmitIn {
  session_ids?: string[]
  total_count?: number | null
  correct_count?: number | null
  wrong_count?: number | null
  unanswered_count?: number | null
  not_entered_count?: number | null
  actual_duration_minutes?: number | null
}

// --- Analytics: سه بلوک جدا (V2-A01) ---

export interface CoverageByResource {
  resource_id: string
  title: string
  subject: string | null
  topics_total: number
  topics_attempted: number
  topics_ratio: number | null
}

export interface CoverageBlock {
  topics_total: number
  topics_attempted: number
  topics_ratio: number | null
  questions_total: number
  questions_attempted: number
  questions_ratio: number | null
  by_resource: CoverageByResource[]
}

export interface AccuracyBlock {
  correct: number
  wrong: number
  unanswered: number
  not_entered: number
  answered_accuracy: number | null
  percent_konkur: number | null
  percent_no_penalty: number | null
  penalty_k: number | null
}

export interface VolumeBlock {
  attempts: number
  sessions: number
  study_minutes: number
  test_duration_minutes: number
  active_days: number
  reviews_done: number
  avg_attempts_per_active_day: number | null
}

export interface TimeBucketRow {
  bucket: string
  attempts: number
  correct: number
  wrong: number
  answered_accuracy: number | null
}

export interface DailyPoint {
  date: string
  date_jalali: string
  attempts: number
  correct: number
  wrong: number
  study_minutes: number
  sessions: number
}

export interface WeaknessRow {
  topic_id: string | null
  topic_title: string | null
  coverage: number | null
  accuracy: number | null
  exam_readiness: number | null
}

/** doc 12.4 — فقط کیفی، هرگز ادعای رتبه دقیق */
export interface KonkursTargetOut {
  has_target: boolean
  target: string | null
  level_fa: string | null
  message_fa: string
  based_on: { answered_accuracy: number | null; topics_ratio: number | null }
}

export interface OverviewOut {
  window: { days: number; start: string; end: string; start_jalali: string; end_jalali: string }
  coverage: CoverageBlock
  accuracy: AccuracyBlock
  volume: VolumeBlock
  time_buckets: TimeBucketRow[]
  daily: DailyPoint[]
  weaknesses: WeaknessRow[]
  konkurs_target: KonkursTargetOut
}

export interface BySubjectItem {
  resource_id: string
  title: string
  subject: string | null
  coverage: { topics_total: number; topics_attempted: number; topics_ratio: number | null; questions_total: number; questions_attempted: number }
  accuracy: { correct: number; wrong: number; answered_accuracy: number | null }
  volume: { attempts: number; sessions: number; duration_minutes: number }
}

export interface ByChapterItem {
  chapter_title: string
  book_title: string | null
  coverage: { topics_total: number; topics_attempted: number; topics_ratio: number | null }
  accuracy: { correct: number; wrong: number; answered_accuracy: number | null }
  volume: { attempts: number }
}

export interface ByTopicItem {
  topic_id: string
  topic_title: string | null
  book_title: string | null
  chapter_title: string | null
  coverage: { questions_total: number; questions_attempted: number; questions_ratio: number | null }
  accuracy: { correct: number; wrong: number; answered_accuracy: number | null }
  volume: { attempts: number; duration_minutes: number }
  exam_readiness: number | null
  weakness: boolean
}

export interface DifficultyItem {
  difficulty: number | null
  difficulty_fa: string
  volume: { attempts: number }
  accuracy: { correct: number; wrong: number; answered_accuracy: number | null }
}

export interface MistakesOut {
  by_error_type: { error_type: string | null; error_type_fa: string; count: number }[]
  top_wrong_topics: { topic_title: string | null; wrong_count: number }[]
  repeated_wrong_questions: { topic_title: string | null; book_title: string | null; question_number: number | null; wrong_count: number; critical: boolean }[]
  notes_total: number
  notes_unlabeled: number
}

// --- Reports (doc 12.5) ---

export interface TopTopicRow {
  topic_id: string | null
  topic_title: string | null
  attempts: number
}

export interface ReportExamRow {
  id: string
  title: string
  kind: ExamKind
  status: ExamStatus
  scheduled_date: string | null
  scheduled_date_jalali: string | null
  percent_konkur: number | null
  percent_no_penalty: number | null
}

export interface DailyReport {
  kind: 'daily'
  date: string
  date_jalali: string
  weekday_fa: string
  coverage: CoverageBlock
  accuracy: AccuracyBlock
  volume: VolumeBlock
  plan: { tasks_total: number; tasks_done: number; study_minutes: number }
  capacity: { available_minutes: number | null; used_minutes: number }
  reviews_done: number
  checkin: Record<string, unknown> | null
  sessions: ExamSessionRow[]
  exams: ReportExamRow[]
  top_topics: TopTopicRow[]
}

export interface WeeklyDayRow {
  date: string
  date_jalali: string
  weekday_fa: string
  is_today: boolean
  attempts: number
  correct: number
  wrong: number
  study_minutes: number
  tasks_done: number
  tasks_total: number
  reviews_done: number
  answered_accuracy: number | null
}

export interface WeeklyReport {
  kind: 'weekly'
  week_start: string
  week_start_jalali: string
  week_end: string
  week_end_jalali: string
  coverage: CoverageBlock
  accuracy: AccuracyBlock
  volume: VolumeBlock
  days: WeeklyDayRow[]
  capacity: { days_with_snapshot: number; available_minutes: number; used_minutes: number; usage_ratio: number | null }
  previous_week: { week_start: string; attempts: number; study_minutes: number; attempts_delta: number; study_minutes_delta: number }
  exams: ReportExamRow[]
  top_topics: TopTopicRow[]
  sessions: ExamSessionRow[]
}

export interface MonthlyWeekRow {
  week_start: string
  week_start_jalali: string
  days: number
  attempts: number
  correct: number
  wrong: number
  study_minutes: number
  tasks_done: number
  tasks_total: number
  answered_accuracy: number | null
}

export interface MonthlyReport {
  kind: 'monthly'
  month: string
  start: string
  end: string
  start_jalali: string
  end_jalali: string
  coverage: CoverageBlock
  accuracy: AccuracyBlock
  volume: VolumeBlock
  weeks: MonthlyWeekRow[]
  exams: ReportExamRow[]
  top_topics: TopTopicRow[]
}

// --- Export (V2-A02: books + attempts همیشه داخل JSON کامل) ---

export interface ExportJsonOut {
  app: string
  version: string
  exported_at: string
  exported_at_jalali: string
  profile: Record<string, unknown>
  settings: Record<string, unknown>
  books: unknown[]
  test_sessions: unknown[]
  attempts: unknown[]
  error_notes: unknown[]
  question_marks: unknown[]
  review_items: unknown[]
  learning_states: unknown[]
  goals: unknown[]
  exams: unknown[]
  plan_tasks: unknown[]
  time_blocks: unknown[]
  capacity_snapshots: unknown[]
  recommendations: unknown[]
  checkins: unknown[]
}

export type PdfReportKind = 'daily' | 'weekly' | 'monthly' | 'summary'

// ---------------------------------------------------------------------------
// Phase 7 — Rewards & Behavior (doc 13): points ledger · streak · badges ·
// habit advice (فقط data_days>=30) · procrastination aid · explain
// ---------------------------------------------------------------------------

export interface StreakOut {
  current: number
  longest: number
  last_active_date: string | null
  grace_days: number
}

export interface HabitAdviceOut {
  available: boolean
  data_days: number
  min_data_days?: number
  median_done?: number
  suggested_daily_tasks?: number
  message_fa?: string
}

export interface ProcrastinationAid {
  kind: 'split' | 'easy_start'
  task_id?: string | null
  task_title?: string | null
  minutes?: number | null
  topic_id?: string | null
  topic_title?: string | null
  avg_completion_rate: number
  message_fa: string
}

export interface LatestCheckin {
  date: string
  date_jalali: string
  energy: number
  focus: number
  motivation: number
  stress: number
  fatigue: number
}

export interface RewardsSummary {
  points_total: number
  points_by_source: Record<string, number>
  streak: StreakOut
  badges: { earned_count: number; total: number; recent: { code: string; title_fa: string }[] }
  habit_advice: HabitAdviceOut
  procrastination: ProcrastinationAid | null
  latest_checkin: LatestCheckin | null
}

export interface BadgeRow {
  code: string
  title_fa: string
  description_fa: string
  kind: string
  target: number
  earned: boolean
  awarded_at: string | null
  progress: { value: number; current: number; target: number }
}

export interface BadgesOut {
  items: BadgeRow[]
  earned_count: number
}
