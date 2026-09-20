# ALEMS — Academic Life & Exam Management System

سامانه مدیریت زندگی تحصیلی و مسیر کنکور — **نسخه 2.0**

منبع حقیقت: [ALEMS_v2_docs](ALEMS_v2_docs/) — اسناد نسخه ۱ فقط برای مرجع مهاجرت.

---

## وضعیت فازها (doc 16)

| فاز | نام | وضعیت |
|-----|-----|--------|
| 0 | Foundation + Motion Shell | ✅ انجام شد |
| 1 | Identity & Student (onboarding، check-in، taught) | ⬜ |
| 2 | Books TOC-only (import فهرست، tree، block_type) | ⬜ |
| 3 | Test Engine (session، range/parity، past import) | ⬜ |
| 4 | Review & Learning (صف، spaced، cluster، learning state) | ⬜ |
| 5 | Planning & Today (capacity، generate-week، override) | ⬜ |
| 6 | Exam & Analytics (exam center، متریک‌ها، export) | ⬜ |
| 7 | Rewards & Recommendation (streak، پیشنهاد، explain) | ⬜ |
| 8 | Polish & Hardening (focus mode، backup، AT کامل) | ⬜ |

---

## اجرا (فاز ۰)

پیش‌نیاز: Python 3.11+ ، Node 18+

```bash
# یک‌بار برای راه‌اندازی
./scripts/setup-dev.sh

# اجرای هم‌زمان Backend (8010) + Frontend (5173)
./scripts/run.sh
```

سپس:

- UI: <http://localhost:5173> (پروکسی Vite → `http://127.0.0.1:8010`)
- API health: <http://localhost:8010/health>
- Swagger: <http://localhost:8010/docs>

پورت‌ها پیش‌فرض سند ۰۳ هستند (Backend **8010**، Frontend **5173**) و با
`ALEMS_BACKEND_PORT` / `ALEMS_FRONTEND_PORT` قابل تغییرند.

### تست‌ها

```bash
# Backend (pytest — envelope، تقویم جلالی، event bus)
cd backend && .venv/bin/python -m pytest

# Frontend (type-check + build)
cd frontend && npm run build
```

---

## ساختار (doc 03 §3.3)

```
ALEMS/
├── backend/
│   ├── app/
│   │   ├── main.py               # app factory + /health
│   │   ├── core/                 # config, security, events, jalali, files, versioning
│   │   ├── db/                   # SQLAlchemy 2 (WAL) — schema فقط با Alembic
│   │   ├── shared/               # envelope پاسخ (doc 06)
│   │   ├── modules/              # 13 ماژول: models/schemas/domain/service/router
│   │   └── api/v1.py             # base /api/v1
│   ├── alembic/                  # نسخه‌گذاری schema
│   ├── tests/                    # pytest
│   └── data/ backups/ exports/ imports/
├── frontend/
│   └── src/
│       ├── app/                  # App, Layout, Theme, BackendStatus
│       ├── components/           # UI kit (Button, Card, Page, EmptyState, Icon)
│       ├── features/             # today, study, tests, review, plan, exams, progress, settings
│       ├── lib/                  # api envelope, dates (jalaali-js + dayjs), health
│       ├── motion/               # variants مشترک Framer Motion (doc 07.4)
│       └── styles/               # tokens.css (doc 07.3) + globals.css
└── scripts/
    ├── setup-dev.sh
    └── run.sh
```

## قواعد کلیدی (غیرقابل مذاکره)

1. TOC-only import کتاب مجاز است (مبحث بدون سوال OK).
2. Coverage ≠ Accuracy ≠ Volume — همیشه جدا.
3. taught ≠ learned · free time ≠ capacity · not-entered ≠ unanswered.
4. Manual Override کاربر بر برنامه خودکار غالب است.
5. ظاهر نسخه ۱ ادامه داده نمی‌شود؛ UI نسخه ۲ + Framer Motion اجباری.
6. Backend 8010 · Frontend 5173 · پروکسی Vite → `http://127.0.0.1:8010`.
7. پیام خطا فارسی · هفته شنبه تا جمعه · Asia/Tehran · Vazirmatn.
