# Changelog — ALEMS

قالب بر اساس «Keep a Changelog» — نسخه‌گذاری معنایی (SemVer).
نسخه schema پایگاه داده جداگانه در جدول `schema_version` ثبت می‌شود.

## [1.0.0] — ۱۴۰۵/۰۶/۲۸ (2026-09-19)

### افزوده شد — نسخه ۱ کامل (MVP + Core)

**فاز ۰ — Foundation**
- ساختار Modular Monolith با ۱۱ ماژول دارای مرز واضح
- Core System: تنظیمات مرکزی (`core/config.py`) + Event Bus سبک (`core/events.py`)
- Database Management: SQLAlchemy 2.0 + SQLite (WAL, foreign_keys) + Alembic
- File Management: مسیرهای استاندارد `data/ backups/ exports/ imports/` + خواندن/نوشتن JSON (`core/files.py`)
- Version Management: ثبت نسخه برنامه و schema در جدول `schema_version` + `/health` (`core/versioning.py`)
- Endpoint سلامت `GET /health` (AT-01)
- سیستم لاگ و مدیریت خطای پایه — پاکت پاسخ `{success, data, error, meta}` با پیام‌های فارسی
- `pyproject.toml` + `requirements.txt` + `package.json` آماده اجرا؛ اجرای کامل با یک دستور (`scripts/run.sh`)

**فاز ۱ — Identity & Profile** (AT-02 تا AT-05)
- ثبت‌نام/ورود/خروج با bcrypt + JWT، مجوز student/admin
- پروفایل دانش‌آموز (پایه/رشته/هدف) + وضعیت روزانه (انرژی ۱-۵، حال، شرایط)

**فاز ۲ — Knowledge Base** (AT-06 تا AT-09)
- درخت دروس رشته→پایه→درس→فصل→مبحث + ۶۷ درس پیش‌فرض
- وارد کردن کتاب تست JSON با اعتبارسنجی فارسی + تشخیص کتاب تکراری

**فاز ۳ — Activity & Review** (AT-10 تا AT-14)
- ثبت دسته‌ای تست + تیک‌های چندگانه + دفترچه خطا (۴ نوع اشتباه)
- صف مرور خودکار (غلط + نزده اختیاری + تیک مرور/مهم/سخت) با چرخه ۱-۳-۷-۱۴

**فاز ۴ — Planning** (AT-15 تا AT-18)
- اهداف بلندمدت/ماهانه/هفتگی + بلوک‌های زمانی ثابت
- تولید خودکار برنامه هفتگی (شنبه تا جمعه) + ویرایش دستی + Today Hub

**فاز ۵ — Exam & Analytics** (AT-19 تا AT-26)
- آزمون آزمایشی/امتحان با تایمر؛ درصد کنکوری `(C − ۰.۳۳W)/T×۱۰۰` و بدون غلط
- تحلیل سختی، تحلیل به تفکیک درس/مبحث، آمار نوع اشتباهات
- گزارش روزانه/هفتگی/ماهانه (جلالی) + خروجی PDF فارسی (وزیرمتن+RTL)، Excel، JSON

**فاز ۶ — Backup & Polish** (AT-27 تا AT-31)
- Backup consistent (SQLite backup API) + رمزنگاری AES اختیاری + Restore دومرحله‌ای
- وب‌اپ کامل فارسی RTL با فونت وزیرمتن، تقویم شمسی، Empty Stateها

### تست‌ها
- ۸۷ تست واحد و پذیرش (دامنه + AT-01 تا AT-27)

## [Unreleased]
- پیش‌بینی نسخه ۲: داشبورد مشاور/والد، همگام‌سازی چنددستگاهی، Spaced Repetition پیشرفته
