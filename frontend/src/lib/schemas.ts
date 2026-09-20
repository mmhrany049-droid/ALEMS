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
