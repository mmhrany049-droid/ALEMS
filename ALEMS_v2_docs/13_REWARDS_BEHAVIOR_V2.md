# ۱۳. پاداش و رفتار — نسخه ۲

## ۱۳.۱ Points
رویدادهای امتیازآور:
- تکمیل plan item
- review complete
- test session finish
- check-in روزانه (سقف ۱)

Ledger append-only.

## ۱۳.۲ Streak
- فعالیت معتبر در تقویم شمسی روز
- از دست دادن روز → reset (تنظیمات می‌تواند grace=0 پیش‌فرض)

## ۱۳.۳ Badges
تعریف در seed: کد، عنوان، شرط  
امضای دریافت یکتا per user/badge

## ۱۳.۴ Habit advice
if active_days_with_data < 30: return null  
else: پیشنهاد تعداد کار روزانه بر اساس میانه انجام واقعی

## ۱۳.۵ Procrastination aid
اگر چند روز completion_rate پایین و taskهای بزرگ باز:
پیشنهاد: split یا «شروع با ۵ تست آسان از مبحث X»

## ۱۳.۶ State dimensions
energy, focus, motivation, stress, fatigue, readiness ∈ 0..1 یا ۱..۵  
منبع: check-in (self-report)؛ later می‌توان observed جدا ذخیره کرد
