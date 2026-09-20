# ALEMS — Academic Life & Exam Management System

سامانه مدیریت زندگی تحصیلی و مسیر کنکور — **نسخه 2.0**

منبع حقیقت: [ALEMS_v2_docs](ALEMS_v2_docs/) — اسناد نسخه ۱ فقط برای مرجع مهاجرت.

---

## وضعیت فازها (doc 16)

| فاز | نام | وضعیت |
|-----|-----|--------|
| 0 | Foundation + Motion Shell | ✅ انجام شد |
| 1 | Identity & Student (onboarding، check-in، taught) | ✅ انجام شد |
| 2 | Books TOC-only (import فهرست، tree، block_type) | ✅ انجام شد |
| 3 | Test Engine (session، range/parity، past import) | ✅ انجام شد |
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
cd backend && .venv/bin/python -m pytest   # pytest — 86 تست: envelope، تقویم جلالی، health، auth، student، taught، books/TOC-only، test engine
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

## معیار پذیرش فاز ۲ (خود-بررسی)

- [x] `POST /resources/import-book` فایل **فقط‌فهرست بدون هیچ question** را موفق وارد می‌کند (questions غایب یا `[]` در هر سطحی)
- [x] خطای «باید حداقل یک سوال داشته باشد» **دیگر وجود ندارد** (تست صریح روی متن پاسخ)
- [x] topic بدون سوال مستقیم و فقط با subtopics → موفقیت
- [x] block_type: `topic|mixed|chapter_exam|checkup|konkur|other` + **استنتاج از عنوان** (کنکور/آزمون/جامع/چکاپ/مخلوط)؛ مقدار صریح بر استنتاج غلبه می‌کند
- [x] duplicate (title+publisher) → **409 فارسی با گزینه به‌روزرسانی** (`replace=true` جایگزین می‌کند؛ taught ردیف‌های قدیمی پاک می‌شود)
- [x] `GET /resources` + `GET /resources/{id}/tree` (badge نوع بلوک، شمار سوال، taught و taught_state با حالت «قسمتی» — doc 08 §8.8)
- [x] `GET /resources/import-book/schema` — راهنمای ساختار با مثال TOC-only
- [x] اگر سوال باشد: `number` و `answer` الزامی (۴۲۲ فارسی مسیردار)؛ answer_keys نسخه‌دار (doc 05)
- [x] taught cascade با درخت واقعی: parent→child آبشاری، `False` نواده‌ها را برنمی‌گرداند
- [x] Frontend: صفحه Import (drag/drop JSON + paste + پیش‌نمایش شمارش + نمونه)، درخت کتاب در Study با badge، EmptyState با CTA
- [x] Migration Alembic 0003 (resources/topics/questions/answer_keys + ایندکس حیاتی topics(resource_id, block_type))
- [x] 66/66 pytest سبز · tsc + vite build سبز · آزمون زنده ۱۰/۱۰ از طریق پروکسی 5173

## معیار پذیرش فاز ۳ (خود-بررسی)

- [x] `POST /test-sessions` با range + parity (any/odd/even) + count + difficulty — **V2-T01: range+odd فقط فردها**
- [x] اگر بعد از فیلتر سوالی نماند → ۴۲۲ فارسی: «فقط X سوال با این شرایط وجود دارد.» (doc 09 §9.2)
- [x] timed/untimed — timed بدون planned_duration رد می‌شود
- [x] `POST /test-sessions/{id}/records` — ثبت سریع؛ **history append-only (V2-T05)**: تکرار سوال ردیف جدید می‌سازد، scoring آخرین ردیف را می‌بیند، snapshots (کلید/نسخه/شماره/موضوع) روی attempt
- [x] `POST /test-sessions/{id}/finish` — **ایدمپوتنت (V2-T02)**: بار دوم همان snapshot بدون رویداد؛ records بعد از finish → ۴۰۹ «تاریخچه قفل است»
- [x] درصد کنکوری **(C − k·W)/T×100** با k=0.33 از settings + درصد بدون منفی C/T×100؛ T=0 → null؛ **درصد منفی نمایش داده می‌شود** — نمونه استاندارد V2-T04: T=10، C=5، W=3 → 40.1 و 50.0
- [x] status: answered|unanswered|**not_entered** — **V2-T03: past import با not_entered**؛ تکمیل بعدی «همان attempt» را answered می‌کند (نه duplicate) و درصد به‌روز می‌شود
- [x] past import سوال/کلید نبوده را می‌سازد (answer_keys نسخه‌دار append-only) — کتاب TOC-only هم پوشش داده می‌شود
- [x] time tracking (doc 09 §9.4): duration per attempt + aggregate per topic (میانگین)؛ untimed → مدت بعد از finish پرسیده می‌شود (پیش‌فرض از تایمر UI)
- [x] دفترچه خطا پایه: هر غلط خودکار یک ردیف + `PUT` نوع اشتباه (بی‌دقتی/مفهومی/روش/فراموشی/سایر) و یادداشت
- [x] Frontend: تب‌های آزمون جدید (preview زنده بازه با شماره‌ها) / تاریخچه (+ادامه جلسه ناتمام) / نتایج قدیمی (ردیف‌ساز) / دفترچه خطا؛ runner با تایمر و ثبت تک‌کلیکی درست/غلط/نزده؛ ScoreCard با ۴ شمارش **جدا** (Coverage≠Accuracy≠Volume)
- [x] Migration Alembic 0004 (test_sessions/attempt_results/error_notes + ایندکس حیاتی attempts(student_id, solved_at)؛ FKها SET NULL تا تاریخچه با حذف کتاب نرود)
- [x] 86/86 pytest سبز · tsc + vite build سبز · آزمون زنده ۱۱/۱۱ از طریق پروکسی 5173

## قواعد کلیدی (غیرقابل مذاکره)

1. TOC-only import کتاب مجاز است (مبحث بدون سوال OK).
2. Coverage ≠ Accuracy ≠ Volume — همیشه جدا.
3. taught ≠ learned · free time ≠ capacity · not-entered ≠ unanswered.
4. Manual Override کاربر بر برنامه خودکار غالب است.
5. ظاهر نسخه ۱ ادامه داده نمی‌شود؛ UI نسخه ۲ + Framer Motion اجباری.
6. Backend 8010 · Frontend 5173 · پروکسی Vite → `http://127.0.0.1:8010`.
7. پیام خطا فارسی · هفته شنبه تا جمعه · Asia/Tehran · Vazirmatn.
