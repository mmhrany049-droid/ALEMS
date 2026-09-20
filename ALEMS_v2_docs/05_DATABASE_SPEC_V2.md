# ۵. پایگاه داده — ALEMS نسخه ۲

## اصول
- SQLite پیش‌فرض + WAL
- UUID یا Integer PK یکدست در کل پروژه (انتخاب: UUID رشته‌ای)
- JSON برای متادیتا و آیتم‌های انعطاف‌پذیر
- Soft-delete فقط جایی که سند صریح گفته

## جداول اصلی (افزون بر V1)

### block_type روی topics
- topics.block_type: `topic|mixed|chapter_exam|checkup|konkur|other`
- topics.is_structural: bool (گره فقط‌ساختار)

### taught_topics
- id, student_id, topic_id, taught (bool), updated_at
- یکتایی (student_id, topic_id)

### answer_keys
- id, question_id, answer, version, created_at
- سوال به آخرین نسخه key برای نمره‌دهی فعلی وصل است؛ تاریخچه attempt نسخه زمان خودش را نگه می‌دارد

### test_sessions
- id, student_id, mode (timed/untimed/past), planned_duration, actual_duration
- started_at, finished_at, source, exam_id nullable

### attempt_results (تقویت test_records)
- status: answered|unanswered|not_entered
- result: correct|wrong|blank|unknown
- answer_key_version
- duration_seconds nullable

### learning_states
- student_id, topic_id
- coverage, accuracy, retention_est, recency_score, repeated_error_score
- exam_readiness, confidence, updated_at

### capacity_snapshots
- student_id, date, school_minutes, class_minutes, available_study_minutes
- estimated_capacity_tasks, source

### recommendations
- id, student_id, date, payload JSON, reasons JSON, status (suggested|accepted|rejected|edited)

### priority_snapshots
- student_id, week_start, items JSON

### rewards
- points_ledger, streaks, badges, badge_awards

### share_links (پایه)
- id, owner_id, audience (advisor|parent), scope JSON, token, expires_at

## ایندکس‌های حیاتی
- attempts (student_id, solved_at)
- learning_states (student_id, topic_id)
- review_queue (student_id, status, scheduled_date)
- topics (resource_id, block_type)

## Migration
- از V1 با `17_MIGRATION_FROM_V1.md`
- هر تغییر schema فقط با Alembic
