# ۳. معماری سیستم — ALEMS نسخه ۲

## ۳.۱ سبک معماری

**Modular Monolith** با لایه‌های:

```
Presentation (React)
    ↓ HTTP JSON
Application (Use-cases / Services)
    ↓
Domain (قوانین خالص، بدون I/O)
    ↓
Infrastructure (DB, files, PDF, backup)
```

هر ماژول Backend:
`models.py` · `schemas.py` · `domain.py` · `service.py` · `router.py`

## ۳.۲ استک

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- Pydantic v2
- Alembic
- SQLite پیش‌فرض (WAL) — PostgreSQL با DATABASE_URL
- bcrypt + JWT
- openpyxl · reportlab/weasyprint · pyzipper

### Frontend
- React 18 + Vite + TypeScript
- Tailwind CSS
- **Framer Motion** برای انیمیشن (اجباری در V2)
- TanStack Query
- React Router
- Recharts
- jalaali-js + dayjs
- Vazirmatn

### پیش‌فرض پورت (برای جلوگیری از مشکل ویندوز)
- Backend: **8010**
- Frontend: **5173**
- پروکسی Vite → `http://127.0.0.1:8010`

## ۳.۳ ساختار فولدر

```
ALEMS/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── core/           # config, security, events, jalali, files, versioning
│   │   ├── db/
│   │   ├── shared/
│   │   ├── modules/
│   │   │   ├── identity/
│   │   │   ├── student/
│   │   │   ├── academic/     # books, topics, questions, import
│   │   │   ├── activity/     # tests, marks, errors, sessions
│   │   │   ├── review/       # queue, spaced, cluster
│   │   │   ├── planning/     # goals, capacity, plans, today
│   │   │   ├── exam/
│   │   │   ├── analytics/
│   │   │   ├── rewards/
│   │   │   ├── report/
│   │   │   ├── export/
│   │   │   ├── backup/
│   │   │   └── settings/
│   │   └── api/v1.py
│   ├── alembic/
│   ├── samples/
│   ├── tests/
│   └── data/ backups/ exports/ imports/
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/     # UI kit + motion wrappers
│       ├── features/
│       ├── lib/
│       ├── hooks/
│       ├── styles/
│       └── motion/         # variants انیمیشن مشترک
└── scripts/
    ├── setup-dev.sh
    └── run.sh              # پیش‌فرض پورت 8010
```

## ۳.۴ Event Bus

رویدادهای دامنه (حداقلی):
- `test_records.created`
- `question_marks.changed`
- `review.completed`
- `plan.updated`
- `exam.finished`
- `checkin.submitted`

مصرف‌کنندگان: review rebuild، rewards، analytics cache باطل‌سازی.

## ۳.۵ تقویم و زمان

- ذخیره: UTC یا ISO
- نمایش: جلالی
- هفته: ۰=شنبه … ۶=جمعه
- timezone پیش‌فرض: Asia/Tehran

## ۳.۶ امنیت

- bcrypt password
- JWT access
- Backup اختیاری AES
- هیچ ارسال داده به سرور خارجی در هسته

## ۳.۷ استراتژی UI Motion

- کتابخانه: Framer Motion
- مدت پایه: 200–350ms
- easing: easeOut برای ورود، easeInOut برای جابه‌جایی
- کاهش حرکت اگر `prefers-reduced-motion`
- انیمیشن باید معنا داشته باشد (نه تزئینی صرف)
