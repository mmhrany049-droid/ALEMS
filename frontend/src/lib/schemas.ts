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
