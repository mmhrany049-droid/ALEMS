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
| 4 | Review & Learning (صف، spaced، cluster، learning state) | ✅ انجام شد |
| 5 | Planning & Today (capacity، generate-week، override) | ✅ انجام شد |
| 6 | Exam & Analytics (exam center، متریک‌ها، export) | ✅ |
| 7 | Rewards & Recommendation (streak، پیشنهاد، explain) | ✅ |
| 8 | Polish & Hardening (focus mode، backup، AT کامل) | ✅ |

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
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
# migrationها خودکار هنگام startup اجرا می‌شوند (alembic upgrade head — idempotent)

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
pip install -r requirements.txt   # شامل tzdata — برای Asia/Tehran روی ویندوز الزامی است
cd ..\frontend
npm install

# Terminal 1 — Backend
cd backend
.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
# migrationها خودکار هنگام startup اجرا می‌شوند

# Terminal 2 — Frontend
cd frontend
npm run dev
```

### خطایابی سریع

| خطا | علت و راه‌حل |
|---|---|
| `ZoneInfoNotFoundError: No time zone found with key Asia/Tehran` (ویندوز/کانتینر slim) | ویندوز دیتابیس IANA timezone ندارد → `pip install tzdata` (در `backend/requirements.txt` هست؛ بعد از `git pull` یک‌بار `pip install -r requirements.txt` بزنید). |
| `sqlite3.OperationalError: no such table: app_metadata` | دیتابیس migrate نشده — از این نسخه به بعد migration خودکار در startup انجام می‌شود؛ دستی: `cd backend && alembic upgrade head`. |
| پورت 8010/5173 اشغال | پروسه قبلی را ببندید یا `PORT`/`FRONTEND_PORT` را در `.env` عوض کنید. |

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
cd backend && .venv/bin/python -m pytest   # pytest — 163 تست: …، rewards، backup/restore
cd frontend && npm run build               # type-check + build

# روی سرور در حال اجرا (پورت 8010):
python3 scripts/v2_acceptance.py           # چک‌لیست پذیرش doc 15 — هر ۲۶ ردیف (V2-B/T/R/P/A/U/S)
python3 scripts/day_one_scenario.py        # سناریوی «روز اول دانش‌آموز» — ثبت‌نام تا پشتیبان‌گیری
```

### نمونه‌ها

- `examples/toc-only-book.json` — کتاب **فقط فهرست** (بدون هیچ سوال؛ شامل topic فقط با subtopics و
  عنوان‌های «آزمون جامع»/«کنکور» برای استنتاج block_type) — با `POST /api/v1/resources/import-book`
  یا drag/drop در صفحه «وارد کردن کتاب» واردش کنید.

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

## معیار پذیرش فاز ۴ (خود-بررسی)

- [x] صف مرور از **غلط‌ها + تیک‌ها** (review/important/hard)؛ «نزده» فقط اگر `include_blank_in_review` روشن باشد (doc 10 §10.1، doc 08 §8.4)
- [x] چرخه **۱-۳-۷-۱۴ از settings** (قابل تغییر از `PUT /settings` — فوراً مؤثر)؛ هر complete → برنامه‌ریزی بعدی؛ پایان چرخه → **absorbed** (بازگشت فقط با غلط جدید)
- [x] **critical اگر غلط ≥ ۲** روی همان سوال (V2-R03) · postpone → تاریخ جابه‌جا، status=pending (V2-R04)
- [x] **rebuild خودکار با event** بعد از finish تست/past import (publish بعد از commit — مصرف‌کننده session خودش را دارد)؛ `POST /reviews/rebuild` دستی هم idempotent بدون duplicate
- [x] **cluster suggestion** (doc 10 §10.3): خوشه‌های ≥ `min_cluster` با هم، سقف `max_daily_review`، اولویت critical و overdue
- [x] **learning_states per topic** (doc 10 §10.4): coverage/accuracy/retention/recency/repeated_error/exam_readiness/confidence — همه فرمول‌ها در `review/domain.py` خالص و unit-test شده (بدون hard-code پراکنده)
- [x] weakness **ترکیبی** است نه تک‌سیگنال (doc 10 §10.5): دقت پایین ∧ خطای تکراری بالا ∧ پوشش ناکافی ∧ اطمینان کافی
- [x] تیک‌ها: `GET/PUT /questions/{id}/marks` + رویداد `question_marks.changed` + ورود فوری به صف (V2-R01)
- [x] Frontend: صفحه مرور با **stagger animation** صف (doc 07.4 #2)، کارت‌های cluster و وضعیت یادگیری با بارهای پیشرفت؛ toggle تیک‌ها در SessionRunner؛ کارت تنظیمات مرور/جریمه در Settings
- [x] Migration Alembic 0005 (question_marks/review_queue/learning_states + ایندکس‌های حیاتی doc 05)
- [x] 107/107 pytest سبز · vite build سبز · آزمون زنده ۲۹/۲۹ روی سرور واقعی

## معیار پذیرش فاز ۵ (خود-بررسی)

- [x] **time blocks مدرسه/کلاس/وقت آزاد** — `GET/PUT /time-blocks` (ورودی «HH:MM» یا دقیقه)؛ بلوک‌ها ورودی ظرفیت‌اند (doc 11.2)
- [x] **school override** ظرفیت را عوض می‌کند (V2-P02): `POST /school-override` با بلوک مدرسه یا `school_off`؛ capacity.source=override
- [x] **capacity محاسبه‌شده** (doc 11.2): بلوک‌های روز + override + میانگین انجام ۷ روز اخیر + state factor وزن‌پایین (check-in) → `available_minutes` / `suggested_task_count` / `suggested_session_count` (وعده ۶۰–۱۲۰ دقیقه) — «وقت آزاد ≠ ظرفیت»
- [x] **generate-week با pipeline دوازده‌مرحله‌ای ثابت و لاگ‌شده** (doc 11.3): load_context → exams → goals → taught_filter → learning_states → review_demand → priority_items → capacity_per_day → allocate_tasks → overload_check → explain → save_suggested؛ خروجی **پیشنهاد است نه قطعی** (locked=false، §8.7)
- [x] **manual override کامل** (doc 11.4): افزودن/حذف (PUT روز)، جابه‌جایی (move-task با تاریخ شمسی/میلادی)، split، merge هم‌روز، status (done/skipped/pending)، **lock** — ویرایش دستی همیشه برنده است
- [x] **کار قفل‌شده بعد از regenerate می‌ماند** (V2-P03): فقط `source=generated ∧ locked=false` حذف می‌شود؛ `kept_locked` در پاسخ گزارش می‌شود
- [x] **recovery بدون dump روی فردا** (V2-P04، doc 11.5): بحرانی‌ها (review/weakness) زودتر، بقیه با سقف `ceil(n/روزهای باقی‌مانده)` پخش می‌شوند؛ `tomorrow_share` در پاسخ — هرگز ۱۰۰٪ روی فردا
- [x] **GET /today کامل** (V2-P01، doc 07.6 ≥۵ بخش): greeting + check-in + ظرفیت + کارهای امروز + مرور سررسیده + پیشنهاد روز + sparkline هفت روز + نوار هفته (+ upcoming_exams فاز ۶)
- [x] **recommendation = یک اقدام مشخص امروز** با accept/reject (doc 11.6) و **≥۱ دلیل با کد قابل ترجمه فارسی** (§8.10 — reasons: [{code, fa}])
- [x] **priority هفته** (doc 11.6): `GET /priority/week` از PrioritySnapshot (upsert هر generate)؛ هدف CRUD با تاریخ شمسی
- [x] Frontend: **Today Hub با داده واقعی + motion cascade** (todayCascade/todayBlock — doc 07.4 #5)، صفحه برنامه با نوار هفته، انیمیشن ۱۲ مرحله planner (plannerStep #8)، ویرایشگر بلوک زمانی، lock/split/merge/move/status، نتیجه recovery
- [x] تاریخ شمسی در URL و body (`/plans/1405-06-29` ≡ `/plans/2026-09-20`)؛ پیام‌های خطا فارسی
- [x] Migration Alembic 0006 (goals/time_blocks/capacity_snapshots/plan_tasks/plan_runs/priority_snapshots/recommendations)
- [x] 126/126 pytest سبز · vite build سبز · آزمون زنده ۶۷/۶۷ روی سرور واقعی

## معیار پذیرش فاز ۶ (خود-بررسی)

- [x] **Exam Center کامل** (doc 12.2): `CRUD /exams` + `POST /exams/{id}/start|submit` + `GET /exams/{id}/result`؛ چرخه planned → in_progress → finished (+ cancelled با امکان بازگشت)؛ finished سند تغییرناپذیر است؛ انواع mock/school_subject/free با برچسب فارسی
- [x] **ثبت نتیجه دو مسیره**: merge چند جلسه تست (session_ids) یا شمارش دستی (total/correct/wrong/unanswered + مدت واقعی)؛ `actual_topic_ids` از جلسات پر می‌شود
- [x] **scoring کنکوری/بدون جریمه همیشه جدا** (doc 08 §8.1): `percent_konkur = (C − k·W)/T·100` و `percent_no_penalty = C/T·100` با k از settings (پیش‌فرض ۰٫۳۳)؛ T=0 → null؛ **درصد منفی نمایش داده می‌شود** (نمایش ۰ نمی‌شود)
- [x] **V2-A01 (قید ۲) در همه‌جا**: `GET /analytics/overview` همیشه سه بلوک جدا `coverage` (از ابتدا تا امروز) / `accuracy` (پنجره) / `volume` (پنجره) برمی‌گرداند — هرگز یک عدد قاطی؛ T از ستون‌های جلسه می‌آید پس «بی‌پاسخ ≠ واردنشده ≠ خالی» در دقت گم نمی‌شود (قید ۳)
- [x] **برش‌های تحلیل** (doc 12.1): by-subject · by-chapter · by-topic (order=volume|accuracy|readiness) · difficulty · mistakes (انواع خطا، پرتکرارترین مباحث غلط، سوالات با غلط تکراری، یادداشت‌های بدون برچسب) — در هر ردیف هم سه متریک جدا
- [x] **هدف کنکور فقط کیفی** (doc 12.4): level_fa + message_fa بر اساس پوشش/دقت — بدون هیچ ادعای رتبه یا تراز دقیق
- [x] **گزارش‌ها** (doc 12.5): `GET /reports/daily?date=` · `weekly?week_start=` · `monthly?month=` (شمسی یا میلادی)؛ هفتگی = ۷ روز + delta هفته قبل + مصرف ظرفیت + آزمون‌های هفته؛ ماهانه = هفته‌های clip شده
- [x] **Export**: `GET /export/json` کامل (V2-A02 — books با درخت و سوالات + attempts همیشه داخلش) · `/export/excel` هفت شیت فارسی RTL (openpyxl) · `/export/pdf?report=daily|weekly|monthly|summary` راست‌به‌چپ با فونت **وزیرمتن embed** (reportlab + arabic-reshaper + python-bidi) — دانلود با Content-Disposition
- [x] **اتصال به planner**: مرحله exams در generate-week واقعی شد — مباحث آزمون‌های پیش‌رو در اولویت **boost (+۰٫۲، reason=exam_prep)** می‌گیرند؛ بخش ۵ «امروز» = آزمون‌های نزدیک (≤۷ روز) با days_until (doc 07 §7.6)
- [x] Frontend: **ExamsPage** (فرم ثبت، شروع/لغو/حذف، modal ثبت نتیجه دو تب‌ه، کارنامه با دو درصد جدا) + **ProgressPage** (سه کارت متریک جدا، ComposedChart روند روزانه، نمودار کتاب‌ها و سختی، لیست مباحث سه‌متریک، کارت هفتگی، هدف کیفی، تحلیل خطاها، دکمه‌های دانلود JSON/Excel/PDF) با Recharts + Framer Motion
- [x] رویداد `EXAM_FINISHED` بعد از submit منتشر می‌شود؛ پیام‌های خطای فارسی («آزمون پیدا نشد.»، «عنوان آزمون نمی‌تواند خالی باشد.»، …)
- [x] Migration Alembic **0007_exams** (تنها جدول جدید — analytics/report/export ویوی محاسباتی‌اند)
- [x] 138/138 pytest سبز · vite build سبز · آزمون زنده **۴۹/۴۹** روی سرور واقعی (+ E2E از طریق پروکسی Vite)

---

## معیار پذیرش فاز ۷ (خود-بررسی)

- [x] **Points ledger append-only** (doc 13.1): چهار رویداد امتیازآور — تکمیل plan item (۵) · مرور کامل (۲) · اتمام جلسه تست (۱۰) · check-in روزانه (۳، سقف ۱ در روز)؛ امضای یکتایی `(student, source, ref)` → رویداد تکراری/ایدمپوتنت هرگز دوباره امتیاز نمی‌گیرد (un-done→done دوباره امتیاز ندارد)
- [x] **معماری رویدادمحور** (doc 03 §3.4 — rewards مصرف‌کننده event bus است): publish های REVIEW_COMPLETED و CHECKIN_SUBMITTED و PLAN_UPDATED(status) به **router و بعد از commit** منتقل شدند تا مصرف‌کننده با session جدا روی SQLite قفل نوشت نگیرد
- [x] **Streak شمسی** (doc 13.2): فعالیت معتبر در روز شمسی؛ روز از دست رفته → reset؛ `streak_grace_days` از settings (پیش‌فرض ۰، اعتبارسنجی فارسی «روزهای ارفاق…»)؛ current تا پایان امروز از streak دیروز محافظت می‌کند؛ longest بدون grace
- [x] **Badges seed** (doc 13.3 + OD4: ۸ تا ۱۲ نشان): ۱۰ نشان با کد/عنوان/شرط (kind+target) — seed idempotent در startup؛ **امضای دریافت یکتا per user/badge**؛ progress در پاسخ
- [x] **Habit advice فقط اگر data_days ≥ 30** (doc 13.4 + doc 08 §8.9 — زیر ۳۰ روز هرگز نمایش داده نمی‌شود): پیشنهاد تعداد کار روزانه = **میانه انجام واقعی**
- [x] **Procrastination aid ساده** (doc 13.5): completion_rate پایین در ۳ روز اخیر + task بزرگ باز (≥۶۰ دقیقه) → پیشنهاد **split**؛ وگرنه با مبحث ضعیف (readiness<0.6) → **«۵ تست آسان از مبحث X»**
- [x] **Recommendation امروز + دلیل فارسی** (§8.10): aid به‌عنوان منبع پیشنهاد وارد `recommendation_pick` شد (reason codes جدید: procrastination_split / procrastination_start)؛ هر payload حالا **explain_fa** دارد — «چرا این پیشنهاد؟» با عدد و شاهد، حتی برای no_demand
- [x] **State dimensions** (doc 13.6): latest_checkin (خودگزارشی ۱..۵) در summary
- [x] Frontend: کارت **«پیوستگی و پاداش»** در Today Hub (🔥 streak جاری/رکورد/امتیاز + نشان‌های اخیر + habit advice + aid) و دکمه **«چرا این پیشنهاد؟»** با panel بازشو (Framer Motion) روی کارت پیشنهاد؛ فیلد grace در تنظیمات
- [x] Migration Alembic **0008_rewards** (points_ledger/streaks/badges/badge_awards)
- [x] 154/154 pytest سبز · vite build سبز · آزمون زنده **۲۰/۲۰** · E2E از طریق پروکسی Vite

---

## معیار پذیرش فاز ۸ (خود-بررسی) — سخت‌سازی نهایی

- [x] **Backup/Restore کامل** (doc 04 «دستی، خودکار، AES» + doc 06): `POST /backup/create` (برچسب + رمز AES اختیاری با pyzipper) · `GET /backup/list` (sidecar json — بدون باز کردن zip رمزدار) · `POST /backup/restore` · `GET /backup/download/{id}` (فایل خام zip)
- [x] **V2-S01 — دور کامل**: snapshot با sqlite3 backup API (سازگار با WAL)؛ دادهٔ بعد از پشتیبان حذف و دادهٔ قبل از آن **بدون از دست رفتن** برمی‌گردد (userA + کتاب سالم، userB می‌پرد)؛ قبل از جایگزینی `PRAGMA integrity_check` + بررسی alembic_version
- [x] **V2-S02 — تأیید دومرحله‌ای**: `confirm !== true` → ۴۲۲ با پیام فارسی actionable؛ در UI هم ConfirmButton دو مرحله‌ای (doc 07.9)
- [x] AES: رمز غلط → ۴۲۲ «رمز فایل پشتیبان اشتباه است.» · retention خودکار (۲۰ نسخه آخر) · id سخت‌گیرانه در برابر path traversal · `auto_backup` در settings → پشتیبان خودکار در startup
- [x] **Focus Mode** (doc 07.7): overlay تمام‌صفحه روی ناوبری — فقط تایمر + سوالات/کار جاری؛ در SessionRunner (دکمه تمرکز، سوال‌ها + ثبت سریع داخل overlay) و در Today Hub برای «کار جاری» (تایمر + «انجام شد»)؛ **خروج تأییدشده** (Escape هم تأیید می‌خواهد)
- [x] **Motion طبق doc 07 تکمیل شد**: success pulse روی ثبت «درست» (الگوی #3 — قبلاً فقط تعریف بود)، **Toast غیرمزاحم** (doc 07.9 — موفقیت/خطا/اطلاع، auto-dismiss، حداکثر ۳)، checkbox انیمیشنی در کارهای امروز (doc 07.6 #3)
- [x] **Today Hub دقیقاً با ترتیب doc 07.6**: ۱ سلام+check-in · ۲ ظرفیت · ۳ کارهای امروز · ۴ صف مرور ضروری · ۵ **آزمون نزدیک (بلوک مستقل)** · ۶ پیشنهاد روز با «چرا؟» · ۷ خلاصه ۷ روز (sparkline) — و «پیوستگی و پاداش» در انتها
- [x] عملیات مخرب با تأیید دومرحله‌ای: حذف آزمون، حذف کار/بلوک برنامه، بازیابی پشتیبان (doc 07.9)
- [x] **چک‌لیست doc 15 کامل پاس شد — ۲۶/۲۶** با `scripts/v2_acceptance.py` (V2-B01..05 · T01..05 · R01..04 · P01..04 · A01..02 · U01..04 · S01..02)
- [x] `examples/toc-only-book.json` + `scripts/day_one_scenario.py` (سناریوی روز اول: ۱۳ گام سبز روی سرور واقعی)
- [x] 163/163 pytest سبز · tsc + vite build سبز · چک زنده backup ۱۶/۱۶ · E2E از طریق پروکسی Vite
- [x] **قبل از هر migration از V1: پشتیبان بگیر** (doc 17) — از UI: تنظیمات → پشتیبان‌گیری، یا `POST /api/v1/backup/create`

---

## قواعد کلیدی (غیرقابل مذاکره)

1. TOC-only import کتاب مجاز است (مبحث بدون سوال OK).
2. Coverage ≠ Accuracy ≠ Volume — همیشه جدا.
3. taught ≠ learned · free time ≠ capacity · not-entered ≠ unanswered.
4. Manual Override کاربر بر برنامه خودکار غالب است.
5. ظاهر نسخه ۱ ادامه داده نمی‌شود؛ UI نسخه ۲ + Framer Motion اجباری.
6. Backend 8010 · Frontend 5173 · پروکسی Vite → `http://127.0.0.1:8010`.
7. پیام خطا فارسی · هفته شنبه تا جمعه · Asia/Tehran · Vazirmatn.
