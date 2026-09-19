# ALEMS — Academic Life & Exam Management System

**سامانه مدیریت زندگی تحصیلی و مسیر کنکور** برای دانش‌آموزان ایرانی

> ماژولار · آفلاین‌محور · فارسی و RTL · تقویم شمسی · هفته شنبه تا جمعه

---

## ⚡ شروع سریع

```bash
# ۱) راه‌اندازی محیط (Backend + Frontend)
bash scripts/setup-dev.sh

# ۲) اجرای برنامه
bash scripts/run.sh
```

- وب‌اپلیکیشن: **http://localhost:5173**
- API: **http://localhost:8000** (اسناد تعاملی: `/api/docs`)
- ثبت‌نام کن، پروفایل را کامل کن و اولین کتاب تست را وارد کن — کمتر از ۵ دقیقه!

### اجرای تست‌ها

```bash
# Backend — تست دامنه (نمره‌دهی/مرور/جلالی/برنامه‌ریزی) + تست پذیرش AT-01..AT-27
cd backend && .venv/bin/python -m pytest tests/ -v

# Frontend — بررسی تایپ
cd frontend && npx tsc -b
```

---

## 🏗 معماری (Modular Monolith)

```
ALEMS/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI + پاکت پاسخ {success,data,error,meta} + خطاهای فارسی
│   │   ├── core/                 # config · security (bcrypt+JWT) · jalali · Event Bus · logging
│   │   │                         #   files (مسیرهای استاندارد+JSON) · versioning (schema_version)
│   │   ├── db/                   # SQLAlchemy 2.0 (SQLite + WAL)
│   │   ├── shared/               # خطاهای دامنه · صفحه‌بندی · پاسخ استاندارد
│   │   ├── modules/              # مرزهای واضح هر ماژول:
│   │   │   ├── identity/         #   کاربر، نشست JWT، مجوز (student/admin)
│   │   │   ├── student/          #   پروفایل + وضعیت روزانه (انرژی/حال)
│   │   │   ├── academic/         #   درخت دروس، منابع، بانک سوال، وارد کردن کتاب JSON
│   │   │   ├── activity/         #   فعالیت، رکورد تست، تیک‌ها، دفترچه خطا، صف مرور
│   │   │   ├── planning/         #   اهداف، بلوک‌های زمانی، برنامه روز/هفته
│   │   │   ├── exam/             #   آزمون + Scoring (فرمول کنکور)
│   │   │   ├── analytics/        #   تحلیل به تفکیک درس/مبحث/سختی/نوع اشتباه
│   │   │   ├── report/           #   گزارش روزانه/هفتگی/ماهانه (تقویم جلالی)
│   │   │   ├── export/           #   PDF (وزیرمتن + RTL) · Excel · JSON
│   │   │   ├── backup/           #   پشتیبان consistent + رمزنگاری اختیاری + بازگردانی
│   │   │   └── settings/         #   سیاست‌های قابل تنظیم (بدون hard-code)
│   │   └── api/v1.py             # مونتاژ روترها — Base URL: /api/v1
│   ├── alembic/                  # مهاجرت‌ها (migration-first)
│   ├── samples/sample_book.json  # قالب استاندارد کتاب تست
│   ├── tests/                    # ۱۰۰ تست (فاز ۰ + دامنه + پذیرش AT-01..27)
│   ├── requirements.txt          # وابستگی‌ها (هم‌ارز pyproject)
│   └── data/ · backups/ · exports/ · imports/   # مسیرهای استاندارد (خارج از Git)
├── frontend/
│   └── src/
│       ├── features/             # auth · today · study · tests · review · planning · exams · analytics · settings
│       ├── components/           # UI Kit + Toast + EmptyState + Layout (RTL)
│       ├── lib/                  # api client + تقویم جلالی (jalaali-js + dayjs)
│       └── types/
└── scripts/                      # setup-dev.sh · run.sh
```

**هر ماژول Backend** لایه‌بندی دارد: `models.py` (دیتابیس) · `schemas.py` (Pydantic) · `domain.py` (منطق خالص و قابل‌تست) · `service.py` (کاربرد) · `router.py` (API).

---

## 📐 قوانین دامنه (پیاده‌سازی‌شده و تست‌شده)

| قانون | پیاده‌سازی |
|-------|------------|
| درصد کنکوری | `(درست − ۰.۳۳ × غلط) ÷ کل × ۱۰۰` — ضریب از `ScoringPolicy` (تنظیمات)، نه hard-code |
| درصد بدون غلط | `درست ÷ کل × ۱۰۰` |
| تقسیم بر صفر | `total = 0` → درصد `null` |
| نتیجه منفی | با علامت منفی نمایش داده می‌شود |
| هفته ایرانی | شنبه تا جمعه (`day_of_week`: ۰=شنبه … ۶=جمعه) |
| صف مرور | غلط‌ها + نزده‌ها (اختیاری از تنظیمات) + تیک‌های `مرور/مهم/سخت` |
| چند تیک همزمان | هر سوال می‌تواند چندین تیک داشته باشد (unique per type) |
| چرخه مرور | ۱ → ۳ → ۷ → ۱۴ روز (قابل تنظیم از سیاست‌ها) |
| نوع اشتباه | فقط برای «غلط» مجاز: بلد نبودن / فراموشی / بی‌دقتی / کمبود زمان |
| آخرین نتیجه | وضعیت جاری هر سوال = آخرین رکورد |

---

## 🧪 معیارهای پذیرش

- **AT-01 تا AT-27**: پوشش داده شده در `backend/tests/test_api_acceptance.py` (همه پاس)
- **AT-28 تا AT-31** (UI): Today Hub، RTL کامل با فونت وزیرمتن، تاریخ‌های جلالی، Empty Stateهای راهنما

## 🔧 تنظیمات محیطی (اختیاری)

| متغیر | پیش‌فرض | توضیح |
|-------|---------|-------|
| `ALEMS_DATABASE_URL` | SQLite در `backend/data/alems.db` | آماده PostgreSQL |
| `ALEMS_SECRET_KEY` | مقدار توسعه | کلید JWT — در استقرار واقعی عوض کنید |

## 🔒 امنیت و مالکیت داده

- رمز عبور با **bcrypt** هش می‌شود؛ نشست با **JWT** مدیریت می‌شود.
- Backup با API استاندارد SQLite (کپی consistent) + رمزنگاری AES اختیاری.
- خروجی کامل JSON همه جداول کاربر (NFR-06).
- هیچ داده‌ای به سرور خارجی ارسال نمی‌شود (Offline-First).
