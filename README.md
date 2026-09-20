# ALEMS — Academic Life & Exam Management System

سامانه مدیریت زندگی تحصیلی و مسیر کنکور — **نسخه 2.0**

منبع حقیقت: [ALEMS_v2_docs](ALEMS_v2_docs/) — اسناد نسخه ۱ فقط برای مرجع مهاجرت.

---

## وضعیت فازها (doc 16)

| فاز | نام | وضعیت |
|-----|-----|--------|
| 0 | Foundation + Motion Shell | ✅ انجام شد |
| 1 | Identity & Student (onboarding، check-in، taught) | ✅ انجام شد |
| 2 | Books TOC-only (import فهرست، tree، block_type) | ⬜ |
| 3 | Test Engine (session، range/parity، past import) | ⬜ |
| 4 | Review & Learning (صف، spaced، cluster، learning state) | ⬜ |
| 5 | Planning & Today (capacity، generate-week، override) | ⬜ |
| 6 | Exam & Analytics (exam center، متریک‌ها، export) | ⬜ |
| 7 | Rewards & Recommendation (streak، پیشنهاد، explain) | ⬜ |
| 8 | Polish & Hardening (focus mode، backup، AT کامل) | ⬜ |

---

## اجرا

پیش‌نیاز: Python 3.11+ ، Node 18+

### Linux / macOS

```bash
# یک‌بار برای راه‌اندازی
./scripts/setup-dev.sh

# اجرای هم‌زمان Backend (8010) + Frontend (5173)
./scripts/run.sh
```

یا دستی:

```bash
# Terminal 1 — Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

### Windows (PowerShell)

```powershell
# یک‌بار
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
cd ..\frontend
npm install

# Terminal 1 — Backend
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### env های Backend (پیش‌فرض‌ها در `app/core/config.py`)

```
APP_NAME=ALEMS
APP_VERSION=2.0.0
HOST=127.0.0.1
PORT=8010
DATABASE_URL=sqlite:///./data/alems.db
TIMEZONE=Asia/Tehran
```

سپس:

- UI: <http://localhost:5173> (پروکسی Vite → `http://127.0.0.1:8010`)
- API health: <http://127.0.0.1:8010/health> و `/api/v1/health`
- Swagger: <http://127.0.0.1:8010/docs>

> پورت 8000 استفاده **نمی‌شود**؛ پیش‌فرض 8010 است (doc 02 NFR-4).

### تست‌ها

```bash
cd backend && .venv/bin/python -m pytest   # pytest — 49 تست: envelope، تقویم جلالی، health، auth، student، taught
cd frontend && npm run build               # type-check + build
```

---

## معیار پذیرش فاز ۰ (خود-بررسی)

- [x] `http://127.0.0.1:8010/health` JSON درست (envelope doc 06 + `status/app/version`)
- [x] `http://localhost:5173` باز می‌شود RTL (Vazirmatn، `dir=rtl`)
- [x] درخواست health از UI موفق است (پروکسی Vite → 127.0.0.1:8010؛ بدون ETIMEDOUT)
- [x] تغییر تم dark/light کار می‌کند (localStorage)
- [x] page transition با Framer Motion (pageVariants روی همه صفحات)
- [x] پورت 8000 استفاده نشده
- [x] ساختار پوشه doc 03 §3.3 · Alembic با revision پایه · پوشه‌های data/backups/exports/imports
- [x] Error envelope یکسان با پیام فارسی
- [x] requirements.txt کامل و نسخه‌دار
- [x] اسکلت Today: سلام + کارت ظرفیت + کارهای امروز (mock) + بلوک مرور + cascade

## معیار پذیرش فاز ۱ (خود-بررسی)

- [x] ثبت‌نام و ورود کامل (bcrypt + JWT HS256؛ stateless؛ logout = client token را رها می‌کند)
- [x] پروفایل دانش‌آموز: پایه / رشته / هدف کنکور (PUT /students/me)
- [x] check-in روزانه (energy/focus/motivation/stress/fatigue، 1..5) — **دو بار در یک روز = upsert، نه duplicate** (date = روز تهران)
- [x] GET /students/me/state — today / last / data_days + تاریخ شمسی
- [x] Taught topics GET/PUT (آبشاری ساده؛ cascade برای فاز ۲ آماده) — **بدون mock topic id**؛ UI آماده + API واقعی
- [x] توکن در client: memory + localStorage (`alems.token`)؛ 401 → پاک‌سازی خودکار
- [x] پیام خطا فارسی (401/409/422/404 + خطاهای فرم)
- [x] Frontend: صفحه Auth با motion، Onboarding ۴ مرحله‌ای، کارت check-in روی Today، پنل taught روی Study، خروج از Settings
- [x] Migration Alembic 0002 (users/students/checkins/taught_topics) — فقط از طریق Alembic
- [x] 49/49 pytest سبز · tsc + vite build سبز

## قواعد کلیدی (غیرقابل مذاکره)

1. TOC-only import کتاب مجاز است (مبحث بدون سوال OK).
2. Coverage ≠ Accuracy ≠ Volume — همیشه جدا.
3. taught ≠ learned · free time ≠ capacity · not-entered ≠ unanswered.
4. Manual Override کاربر بر برنامه خودکار غالب است.
5. ظاهر نسخه ۱ ادامه داده نمی‌شود؛ UI نسخه ۲ + Framer Motion اجباری.
6. Backend 8010 · Frontend 5173 · پروکسی Vite → `http://127.0.0.1:8010`.
7. پیام خطا فارسی · هفته شنبه تا جمعه · Asia/Tehran · Vazirmatn.
