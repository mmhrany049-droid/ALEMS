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
