# ۹. پرامپت‌های هوش مصنوعی کدساز (Coding Agent Prompts) — نسخه ۱

این فایل شامل پرامپت‌های آماده برای دادن به هوش مصنوعی کدساز است.
هر پرامپت مربوط به یک فاز یا ماژول مشخص است.

---

## پرامپت پایه (همیشه در ابتدا بدهید)

```
تو یک مهندس نرم‌افزار ارشد هستی که باید سیستم ALEMS (Academic Life & Exam Management System) را پیاده‌سازی کنی.

اسناد پروژه در پوشه ALEMS_v1_docs قرار دارد. حتماً این فایل‌ها را رعایت کن:
- 01_VISION_SCOPE.md
- 03_SYSTEM_ARCHITECTURE.md
- 04_MODULE_CATALOG.md
- 05_DATABASE_SPEC.md
- 06_API_CONTRACT.md
- 08_BUSINESS_RULES_EDGE_CASES.md

تکنولوژی‌ها:
- Backend: Python + FastAPI + SQLAlchemy + Pydantic + Alembic + SQLite
- Frontend: React + Vite + TypeScript + Tailwind + jalaali
- زبان UI: فارسی و RTL
- تقویم: شمسی، هفته شنبه تا جمعه

قوانین مهم:
- کد ماژولار بنویس
- از hard-code کردن منطق کسب‌وکار خودداری کن
- تمام APIها مطابق قرارداد باشند
- تست‌های واحد برای منطق دامنه بنویس
- پیام‌های خطا فارسی باشند
```

---

## پرامپت فاز ۰ — Foundation

```
فاز ۰ را پیاده‌سازی کن:

1. ساختار پروژه Backend و Frontend مطابق 03_SYSTEM_ARCHITECTURE.md
2. ماژول‌های Core، Database، File Management، Version Management
3. اتصال SQLite + Alembic
4. سیستم تنظیمات مرکزی
5. Endpoint سلامت (/health)
6. ساختار لاگ و مدیریت خطای پایه

خروجی مورد انتظار:
- پروژه قابل اجرا
- migration اولیه
- تست سلامت موفق
```

---

## پرامپت فاز ۱ — هویت و پروفایل

```
فاز ۱ را پیاده‌سازی کن:

- User Identity + Session + Permission
- Student Profile
- Student State (ثبت انرژی و حال روزانه)
- صفحه تنظیمات پروفایل در Frontend
- احراز هویت کامل (ثبت‌نام، ورود، خروج)

مطابق 05_DATABASE_SPEC و 06_API_CONTRACT عمل کن.
```

---

## پرامپت فاز ۲ — دانش آموزشی و بانک سوال

```
فاز ۲ را پیاده‌سازی کن:

- Academic Knowledge Base (درخت درس/فصل/مبحث)
- Resource Management
- Book Import (از JSON)
- Question Bank + Classification

یک قالب JSON نمونه برای کتاب تست هم ارائه بده و endpoint وارد کردن را کامل پیاده کن.
```

---

## پرامپت فاز ۳ — فعالیت، تست و مرور

```
فاز ۳ را پیاده‌سازی کن:

- Learning Activity
- Test Record
- Question Marking
- Error Notebook
- Review Management (صف مرور + قوانین کسب‌وکار)

ثبت دسته‌ای تست و بازسازی صف مرور را کامل پشتیبانی کن.
```

---

## پرامپت فاز ۴ — برنامه‌ریزی

```
فاز ۴ را پیاده‌سازی کن:

- Goal Management
- Calendar (شمسی)
- Time Management (بلوک‌های زمانی)
- Planning (برنامه روزانه و هفتگی)

Today Hub را با داده‌های واقعی این فاز متصل کن.
```

---

## پرامپت فاز ۵ — آزمون و تحلیل

```
فاز ۵ را پیاده‌سازی کن:

- Exam Management
- Scoring (درصد کنکوری و بدون غلط)
- Difficulty Performance
- Analytics پایه
- Visualization (نمودارهای اصلی)
- Report و Export (PDF / Excel / JSON)

قوانین نمره‌دهی در 08_BUSINESS_RULES_EDGE_CASES.md را دقیقاً رعایت کن.
```

---

## پرامپت فاز ۶ — Backup و پرداخت نهایی

```
فاز ۶ را پیاده‌سازی کن:

- Backup & Restore کامل
- تنظیمات نهایی
- بهبود Empty States و پیام‌های خطا
- تست‌های پذیرش اصلی مطابق 10_ACCEPTANCE_TESTS.md
- مستندسازی نحوه اجرا در README اصلی پروژه
```

---

## نکات برای استفاده بهتر از پرامپت‌ها

1. همیشه پرامپت پایه را همراه با پرامپت فاز بدهید.
2. بعد از هر فاز، از عامل بخواهید تست‌های مربوطه را اجرا و گزارش کند.
3. اگر تغییری در اسناد دادید، نسخه جدید اسناد را دوباره به عامل بدهید.
4. برای بخش‌های پیچیده (مثل Book Import یا Scoring) می‌توانید پرامپت جداگانه و دقیق‌تر بنویسید.
