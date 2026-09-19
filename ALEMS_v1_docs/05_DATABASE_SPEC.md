# ۵. مشخصات پایگاه داده (Database Spec) — نسخه ۱

## ۵.۱ اصول کلی

- موتور پیش‌فرض: **SQLite**
- ORM: SQLAlchemy 2.0
- مهاجرت: Alembic
- نام‌گذاری جداول: جمع و snake_case (مثال: `test_records`)
- کلید اصلی: `id` از نوع UUID یا Integer خودکار
- زمان‌ها: ذخیره به صورت UTC یا ISO، نمایش جلالی در لایه UI
- Soft Delete در نسخه ۱ استفاده نمی‌شود (حذف فیزیکی با تأیید کاربر)

---

## ۵.۲ جداول اصلی نسخه ۱

### users
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| username | str unique | |
| password_hash | str | bcrypt |
| role | str | student / admin |
| created_at | datetime | |
| updated_at | datetime | |

### student_profiles
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| user_id | FK → users | |
| full_name | str | |
| grade | str | دهم / یازدهم / دوازدهم / فارغ‌التحصیل |
| field | str | ریاضی / تجربی / انسانی |
| academic_year | str | |
| target_rank | int nullable | |
| target_major | str nullable | |
| created_at | datetime | |

### student_states
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| date | date | تاریخ شمسی معادل |
| energy_level | int | ۱ تا ۵ |
| mood | str nullable | |
| study_condition | str nullable | |
| note | text nullable | |

### subjects (دروس)
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| name | str | |
| field | str | رشته مرتبط |
| grade | str | پایه مرتبط |
| order_index | int | |

### chapters
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| subject_id | FK | |
| title | str | |
| order_index | int | |

### topics
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| chapter_id | FK | |
| title | str | |
| parent_id | FK nullable | برای زیرمبحث |
| order_index | int | |

### resources
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| title | str | |
| type | str | book_test / textbook / note / class / video |
| subject_id | FK nullable | |
| publisher | str nullable | |
| metadata | JSON | |

### questions
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| resource_id | FK | |
| topic_id | FK | |
| number | str | شماره سوال در کتاب |
| correct_answer | str | |
| difficulty | str | easy / medium / hard |
| importance | int | ۱ تا ۵ |
| tags | JSON | |
| extra | JSON | |

### learning_activities
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| type | str | study / test / review / class / school |
| subject_id | FK nullable | |
| resource_id | FK nullable | |
| started_at | datetime | |
| duration_minutes | int | |
| note | text nullable | |

### test_records
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| question_id | FK | |
| result | str | correct / wrong / blank |
| solved_at | datetime | |
| duration_seconds | int nullable | |
| activity_id | FK nullable | |

### question_marks
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| question_id | FK | |
| mark_type | str | important / review / hard / mistake / tip |
| created_at | datetime | |
| unique | (student_id, question_id, mark_type) | |

### error_notes
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| test_record_id | FK | |
| error_type | str | unknown / forgotten / careless / time |
| note | text nullable | |

### review_queue
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| question_id | FK | |
| reason | str | |
| priority | int | |
| scheduled_date | date | |
| reviewed_at | datetime nullable | |
| status | str | pending / done |

### goals
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| type | str | long / monthly / weekly |
| title | str | |
| target_value | str/JSON | |
| start_date | date | |
| end_date | date | |
| status | str | active / completed / cancelled |

### time_blocks
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| day_of_week | int | ۰=شنبه ... ۶=جمعه |
| start_time | time | |
| end_time | time | |
| block_type | str | school / class / study / free |
| title | str nullable | |

### plans
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| date | date | |
| items | JSON | لیست آیتم‌های برنامه |
| status | str | draft / active / done |

### exams
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| student_id | FK | |
| title | str | |
| exam_type | str | mock / subject |
| scheduled_at | datetime | |
| duration_minutes | int | |
| status | str | planned / in_progress / finished |

### exam_questions
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| exam_id | FK | |
| question_id | FK | |
| order_index | int | |

### exam_results
| ستون | نوع | توضیح |
|------|-----|-------|
| id | UUID/PK | |
| exam_id | FK | |
| correct_count | int | |
| wrong_count | int | |
| blank_count | int | |
| percent_konkur | float | |
| percent_no_penalty | float | |
| difficulty_breakdown | JSON | |
| finished_at | datetime | |

### app_settings
| ستون | نوع | توضیح |
|------|-----|-------|
| key | str PK | |
| value | JSON | |

### schema_version
| ستون | نوع | توضیح |
|------|-----|-------|
| version | str | |
| applied_at | datetime | |

---

## ۵.۳ ایندکس‌های پیشنهادی

- `test_records (student_id, solved_at)`
- `test_records (question_id)`
- `question_marks (student_id, question_id)`
- `review_queue (student_id, status, scheduled_date)`
- `questions (resource_id, topic_id)`
- `learning_activities (student_id, started_at)`

---

## ۵.۴ نکات پیاده‌سازی

1. تمام Foreign Keyها باید با `ON DELETE` مناسب تعریف شوند (معمولاً RESTRICT یا CASCADE کنترل‌شده).
2. فیلدهای JSON برای انعطاف‌پذیری در متادیتا و آیتم‌های برنامه استفاده می‌شوند.
3. برای عملکرد بهتر در SQLite، از ایندکس‌های ترکیبی روی فیلترهای پرتکرار استفاده شود.
4. Backup باید شامل کل فایل SQLite + فایل‌های پیوست (در صورت وجود) باشد.
