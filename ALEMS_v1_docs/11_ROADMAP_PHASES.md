# ۱۱. نقشه راه فازبندی‌شده (Roadmap) — نسخه ۱

## نمای کلی فازها

| فاز | نام | تمرکز | تخمین |
|-----|-----|-------|-------|
| ۰ | Foundation | هسته، دیتابیس، ساختار پروژه | ۱–۲ هفته |
| ۱ | Identity & Profile | کاربر، پروفایل، وضعیت روزانه | ۱ هفته |
| ۲ | Knowledge Base | دروس، منابع، بانک سوال، وارد کردن کتاب | ۲ هفته |
| ۳ | Activity & Review | ثبت تست، دفترچه خطا، صف مرور | ۲ هفته |
| ۴ | Planning | اهداف، تقویم، برنامه روزانه/هفتگی، Today Hub | ۱.۵–۲ هفته |
| ۵ | Exam & Analytics | آزمون، نمره‌دهی، تحلیل، نمودار، گزارش | ۲ هفته |
| ۶ | Backup & Polish | پشتیبان‌گیری، خروجی، پرداخت نهایی UX | ۱ هفته |

**جمع تقریبی نسخه ۱:** ۸ تا ۱۲ هفته (بسته به سرعت عامل کدساز و بازبینی‌ها)

---

## جزئیات هر فاز

### فاز ۰ — Foundation
**ماژول‌ها:** Core, Database, File Management, Version Management  
**خروجی:** پروژه قابل اجرا + migration + /health  
**تست‌های مرتبط:** AT-01

### فاز ۱ — Identity & Profile
**ماژول‌ها:** User Identity, Session, Permission, Student Profile, Student State  
**خروجی:** ثبت‌نام، ورود، پروفایل کامل، ثبت انرژی روزانه  
**تست‌های مرتبط:** AT-02 تا AT-05

### فاز ۲ — Knowledge Base
**ماژول‌ها:** Academic Knowledge Base, Resource Management, Book Import, Question Bank, Classification  
**خروجی:** درخت دروس + وارد کردن کتاب JSON + لیست سوالات  
**تست‌های مرتبط:** AT-06 تا AT-09

### فاز ۳ — Activity & Review
**ماژول‌ها:** Learning Activity, Test Record, Question Marking, Error Notebook, Review Management  
**خروجی:** ثبت تست دسته‌ای + صف مرور هوشمند  
**تست‌های مرتبط:** AT-10 تا AT-14

### فاز ۴ — Planning
**ماژول‌ها:** Goal Management, Calendar, Time Management, Planning + Daily Check-in و Today Hub  
**خروجی:** برنامه هفتگی + صفحه امروز کاربردی  
**تست‌های مرتبط:** AT-15 تا AT-18 و AT-28

### فاز ۵ — Exam & Analytics
**ماژول‌ها:** Exam Management, Scoring, Difficulty Performance, Analytics, Visualization, Report, Export  
**خروجی:** آزمون کامل + درصد صحیح + نمودار + PDF/Excel  
**تست‌های مرتبط:** AT-19 تا AT-26

### فاز ۶ — Backup & Polish
**ماژول‌ها:** Backup & Restore + بهبودهای UX و پایداری  
**خروجی:** Backup/Restore مطمئن + Empty States + README نهایی  
**تست‌های مرتبط:** AT-27 تا AT-31

---

## ترتیب پیشنهادی کار با هوش مصنوعی کدساز

1. اسناد کامل را در اختیار عامل قرار دهید.
2. پرامپت پایه + پرامپت فاز ۰ را بدهید.
3. پس از اتمام هر فاز، تست‌های مربوطه را اجرا و نتیجه را بررسی کنید.
4. فقط پس از پاس شدن تست‌های فاز جاری، به فاز بعدی بروید.
5. در پایان فاز ۶، کل AT-01 تا AT-31 را یک‌بار دیگر اجرا کنید.

---

## آماده‌سازی برای نسخه ۲ (آینده)

پس از پایدار شدن نسخه ۱، این موارد در اولویت نسخه ۲ قرار می‌گیرند:

- داشبورد مشاور و والد
- Spaced Repetition پیشرفته‌تر
- Weakness Detector قوی‌تر
- همگام‌سازی چنددستگاهی
- سیستم اشتراک‌گذاری کنترل‌شده
- Mock Exam Simulator پیشرفته
- Recommendation هوشمندتر
