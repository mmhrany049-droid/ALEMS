# ۱۱. برنامه‌ریزی و ظرفیت — نسخه ۲

## ۱۱.۱ Today Hub API: GET /today
پاسخ شامل:
- checkin امروز
- capacity خلاصه
- plan items
- review top items
- upcoming exams
- recommendation روز
- week sparkline

## ۱۱.۲ ظرفیت
ورودی‌ها:
- time_blocks روز (مدرسه/کلاس/آزاد)
- school_override
- میانگین completion هفت روز اخیر
- state (energy/focus) اختیاری وزن پایین

خروجی:
- available_minutes
- suggested_task_count
- suggested_session_count (وعده‌ها ۶۰–۱۲۰ دقیقه)

## ۱۱.۳ تولید هفته
Pipeline ثابت (کد باید همین ترتیب را لاگ کند):
1. load context
2. exams
3. goals
4. taught filter
5. learning states
6. review demand
7. priority items
8. capacity per day
9. allocate tasks
10. overload check
11. explain
12. save as suggested (نه locked)

## ۱۱.۴ Manual Override
عملیات: add, remove, move day, split, merge, change count, pin/lock  
Task با lock=true در regenerate حفظ می‌شود.

## ۱۱.۵ Recovery
اگر plan item انجام نشد:
- اولویت بحرانی حفظ
- بقیه پخش در روزهای باقی‌مانده هفته
- ممنوع: انتقال ۱۰۰٪ به فردا

## ۱۱.۶ Priority vs Recommendation
- Priority: چه مباحثی این هفته مهم‌اند (لیست)
- Recommendation: امروز چه کار مشخصی بکن (قابل accept/reject)
