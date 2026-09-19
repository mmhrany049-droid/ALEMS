# ۳. معماری سیستم (System Architecture) — نسخه ۱

## ۳.۱ نمای کلی

ALEMS نسخه ۱ به صورت **Modular Monolith** طراحی شده است:

- یک Backend واحد (FastAPI)
- یک Frontend واحد (React + Vite)
- پایگاه داده SQLite (با امکان ارتقا به PostgreSQL)
- ارتباط داخلی ماژول‌ها از طریق سرویس‌ها و Event Bus ساده

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  Today Hub · Study · Tests · Planning · Analytics · ... │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP / JSON
┌──────────────────────────▼──────────────────────────────┐
│                 Backend (FastAPI)                        │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │
│  │  Core   │ │  User   │ │Academic │ │ Activity│  ...  │
│  │ Modules │ │ Modules │ │ Modules │ │ Modules │       │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │
│                      Event Bus                          │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│              SQLite (+ Alembic Migrations)               │
└─────────────────────────────────────────────────────────┘
```

---

## ۳.۲ تکنولوژی‌ها

### Backend
- Python 3.11+
- FastAPI
- SQLAlchemy 2.0 (ORM)
- Pydantic v2 (اعتبارسنجی)
- Alembic (مهاجرت دیتابیس)
- SQLite (پیش‌فرض) / PostgreSQL (آینده)
- WeasyPrint یا ReportLab (PDF)
- openpyxl (Excel)

### Frontend
- Node.js 20+
- React 18
- Vite
- TypeScript
- Tailwind CSS
- React Router
- TanStack Query (مدیریت داده)
- Recharts یا Chart.js (نمودار)
- jalaali-js + dayjs (تقویم شمسی)
- Vazirmatn (فونت)

### ابزارها
- uv یا poetry (مدیریت وابستگی Python)
- npm / pnpm
- pytest + httpx (تست Backend)
- Vitest + Testing Library (تست Frontend)

---

## ۳.۳ لایه‌های منطقی

| لایه | مسئولیت |
|------|----------|
| **Presentation** | صفحات React و کامپوننت‌ها |
| **Application** | Use-caseها و سرویس‌های سطح بالا |
| **Domain** | منطق کسب‌وکار خالص (قوانین درصد، مرور و...) |
| **Infrastructure** | دیتابیس، فایل، Backup، Export |

---

## ۳.۴ ساختار پیشنهادی فولدر Backend

```
backend/
├── app/
│   ├── main.py
│   ├── core/                 # تنظیمات، امنیت، رویدادها
│   ├── db/                   # session، base، migrations
│   ├── modules/
│   │   ├── identity/
│   │   ├── student/
│   │   ├── academic/
│   │   ├── activity/
│   │   ├── planning/
│   │   ├── exam/
│   │   ├── analytics/
│   │   ├── report/
│   │   └── backup/
│   ├── shared/               # مدل‌های مشترک، exceptionها
│   └── api/                  # روترهای نسخه ۱
├── alembic/
├── tests/
└── pyproject.toml
```

---

## ۳.۵ ساختار پیشنهادی فولدر Frontend

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── components/           # کامپوننت‌های مشترک
│   ├── features/             # هر فیچر یک پوشه
│   │   ├── today/
│   │   ├── study/
│   │   ├── tests/
│   │   ├── planning/
│   │   ├── exams/
│   │   ├── analytics/
│   │   └── settings/
│   ├── lib/                  # api client، utils، calendar
│   ├── hooks/
│   ├── types/
│   └── styles/
├── public/
└── package.json
```

---

## ۳.۶ اصول معماری

1. **ماژولار بودن**: هر ماژول Backend باید مستقل قابل‌فهم و تا حد امکان مستقل از بقیه باشد.
2. **Dependency Rule**: لایه‌های بالاتر فقط به لایه‌های پایین‌تر وابسته باشند.
3. **Event-driven سبک**: تغییرات مهم (ثبت تست، اتمام آزمون) از طریق Event داخلی اعلام شوند.
4. **Schema-first**: تمام ورودی/خروجی API با Pydantic تعریف شود.
5. **Migration-first**: هر تغییر دیتابیس فقط از طریق Alembic.
6. **RTL از روز اول**: تمام UI با `dir="rtl"` و فونت فارسی طراحی شود.

---

## ۳.۷ مدیریت زمان و تقویم

- منطقه زمانی پیش‌فرض: `Asia/Tehran`
- هفته: شنبه تا جمعه
- نمایش تاریخ: جلالی (شمسی)
- ذخیره داخلی: ISO 8601 (میلادی) + فیلد جلالی برای نمایش

---

## ۳.۸ استراتژی Offline

نسخه ۱:
- Frontend تمام داده‌های ضروری را در حافظه و در صورت نیاز IndexedDB نگه می‌دارد.
- Backend روی همان ماشین اجرا می‌شود (localhost).
- همگام‌سازی ابری در نسخه ۱ وجود ندارد.

---

## ۳.۹ امنیت نسخه ۱

- رمز عبور با bcrypt هش می‌شود.
- Session مبتنی بر JWT یا Cookie امن.
- Backup فایل‌ها قابل رمزنگاری اختیاری با رمز کاربر.
- هیچ داده حساسی به سرور خارجی ارسال نمی‌شود.
