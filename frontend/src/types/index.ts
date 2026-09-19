// انواع مشترک Frontend — مطابق قرارداد API
export interface User {
  id: string;
  username: string;
  role: 'student' | 'admin';
  created_at: string;
  last_login_at: string | null;
}

export interface Profile {
  id: string | null;
  full_name: string | null;
  grade: string | null;
  field: string | null;
  academic_year: string | null;
  target_rank: number | null;
  target_major: string | null;
  is_complete: boolean;
}

export const GRADES = ['دهم', 'یازدهم', 'دوازدهم', 'فارغ‌التحصیل'];
export const FIELDS = ['ریاضی', 'تجربی', 'انسانی'];

export interface StudentState {
  id: string;
  date: string;
  energy_level: number;
  mood: string | null;
  study_condition: string | null;
  note: string | null;
  weekday: number;
}

export interface Subject {
  id: string;
  name: string;
  field: string;
  grade: string;
  order_index: number;
}

export interface Chapter {
  id: string;
  subject_id: string;
  title: string;
  order_index: number;
}

export interface Topic {
  id: string;
  chapter_id: string;
  title: string;
  parent_id: string | null;
  order_index: number;
}

export interface Resource {
  id: string;
  title: string;
  type: string;
  subject_id: string | null;
  publisher: string | null;
  question_count?: number;
  created_at: string | null;
}

export interface Question {
  id: string;
  resource_id: string;
  topic_id: string;
  topic_title: string | null;
  chapter_title: string | null;
  subject_name: string | null;
  number: string;
  difficulty: 'easy' | 'medium' | 'hard' | null;
  importance: number;
  tags: string[];
  text: string | null;
}

export type TestResult = 'correct' | 'wrong' | 'blank';
export type MarkType = 'important' | 'review' | 'hard' | 'mistake' | 'tip';
export type ErrorType = 'unknown' | 'forgotten' | 'careless' | 'time';

export interface TestRecord {
  id: string;
  question_id: string;
  result: TestResult;
  solved_at: string;
  duration_seconds: number | null;
  question_number: string | null;
  topic_title: string | null;
  error_type: ErrorType | null;
  error_note: string | null;
}

export interface ReviewItem {
  id: string;
  question_id: string;
  reason: string;
  priority: number;
  scheduled_date: string;
  status: 'pending' | 'done';
  review_count: number;
  reviewed_at: string | null;
  question_number: string | null;
  topic_title: string | null;
  difficulty: string | null;
  marks: string[];
}

export interface Activity {
  id: string;
  type: 'study' | 'test' | 'review' | 'class' | 'school';
  subject_id: string | null;
  resource_id: string | null;
  started_at: string;
  duration_minutes: number;
  note: string | null;
  subject_name?: string | null;
}

export interface Goal {
  id: string;
  type: 'long' | 'monthly' | 'weekly';
  type_label: string;
  title: string;
  target_value: { minutes?: number; hours?: number; subject?: string };
  start_date: string;
  end_date: string;
  status: 'active' | 'completed' | 'cancelled';
}

export interface TimeBlock {
  id: string;
  day_of_week: number; // ۰=شنبه ... ۶=جمعه
  start_time: string;
  end_time: string;
  block_type: 'school' | 'class' | 'study' | 'free';
  title: string | null;
}

export interface PlanItem {
  start: string;
  end: string;
  title: string;
  subject?: string | null;
  type: string;
  done?: boolean;
  goal_id?: string | null;
}

export interface Plan {
  id: string;
  date: string;
  items: PlanItem[];
  status: string;
  summary: { total_minutes: number; by_subject: Record<string, number> };
}

export interface Exam {
  id: string;
  title: string;
  exam_type: 'mock' | 'subject';
  scheduled_at: string;
  duration_minutes: number;
  status: 'planned' | 'in_progress' | 'finished';
  started_at: string | null;
  question_count?: number;
  percent_konkur?: number | null;
  percent_no_penalty?: number | null;
}

export interface DifficultyStat {
  total: number;
  correct: number;
  wrong: number;
  blank: number;
  percent_konkur: number | null;
  percent_no_penalty: number | null;
}

export interface ExamResult {
  correct_count: number;
  wrong_count: number;
  blank_count: number;
  percent_konkur: number | null;
  percent_no_penalty: number | null;
  difficulty_breakdown: Record<string, DifficultyStat>;
}

export interface SubjectStat {
  subject_id?: string;
  subject: string;
  total: number;
  correct: number;
  wrong: number;
  blank: number;
  percent_konkur: number | null;
  percent_no_penalty: number | null;
}

export interface TopicStat extends SubjectStat {
  topic_id: string;
  topic: string;
  chapter: string;
}

export interface MistakeStat {
  error_type: ErrorType;
  label: string;
  count: number;
  share: number;
}

export interface BackupInfo {
  id: string;
  filename: string;
  size_bytes: number;
  created_at: string;
  encrypted: boolean;
}

export const RESULT_LABELS: Record<TestResult, string> = {
  correct: 'درست',
  wrong: 'غلط',
  blank: 'نزده',
};

export const MARK_LABELS: Record<MarkType, string> = {
  important: 'مهم',
  review: 'مرور',
  hard: 'سخت',
  mistake: 'اشتباه',
  tip: 'نکته‌دار',
};

export const MARK_COLORS: Record<MarkType, string> = {
  important: 'bg-amber-100 text-amber-800 border-amber-300',
  review: 'bg-blue-100 text-blue-800 border-blue-300',
  hard: 'bg-purple-100 text-purple-800 border-purple-300',
  mistake: 'bg-red-100 text-red-800 border-red-300',
  tip: 'bg-emerald-100 text-emerald-800 border-emerald-300',
};

export const ERROR_TYPE_LABELS: Record<ErrorType, string> = {
  unknown: 'بلد نبودن',
  forgotten: 'فراموشی',
  careless: 'بی‌دقتی',
  time: 'کمبود زمان',
};

export const DIFFICULTY_LABELS: Record<string, string> = {
  easy: 'آسان',
  medium: 'متوسط',
  hard: 'سخت',
};

export const ACTIVITY_TYPE_LABELS: Record<Activity['type'], string> = {
  study: 'مطالعه',
  test: 'تست‌زنی',
  review: 'مرور',
  class: 'کلاس',
  school: 'مدرسه',
};

export const BLOCK_TYPE_LABELS: Record<TimeBlock['block_type'], string> = {
  school: 'مدرسه',
  class: 'کلاس',
  study: 'مطالعه',
  free: 'آزاد',
};
