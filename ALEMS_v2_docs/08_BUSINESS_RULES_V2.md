# ۸. قوانین کسب‌وکار — ALEMS نسخه ۲

## ۸.۱ نمره‌دهی
```
percent_konkur = (C - k * W) / T * 100
percent_no_penalty = C / T * 100
```
- k پیش‌فرض 0.33 از Settings
- T=0 → null
- درصد منفی نمایش داده می‌شود (سیاست: show_negative=true)

## ۸.۲ وضعیت پاسخ
| وضعیت | معنی |
|-------|------|
| answered + correct/wrong | پاسخ داد و کلید موجود بود |
| unanswered | آگاهانه نزده |
| not_entered | در past import هنوز وارد نشده |

## ۸.۳ Import کتاب
1. questions غایب یا `[]` → مجاز (TOC-only)
2. اگر question هست → number و answer الزامی
3. topic بدون سوال مستقیم و فقط با subtopics → مجاز
4. block_type پیش‌فرض topic؛ از روی عنوان `[آزمون]`/`[کنکور]` قابل استنتاج
5. کتاب تکراری (title+publisher) → 409 با گزینه به‌روزرسانی

## ۸.۴ مرور
- ورود به صف: wrong، تیک review/important/hard، blank اختیاری از settings
- چرخه: ۱→۳→۷→۱۴ (از settings)
- خوشه: حداکثر ۲۵ آیتم صفحه‌روزانه پیشنهاد؛ حداقل خوشه ۸ اگر موجود
- critical: wrong_count_on_question ≥ 2
- postpone مجاز؛ complete شمارنده را جلو می‌برد

## ۸.۵ Coverage / Accuracy / Volume
- Coverage: نسبت واحدهای پوشش‌یافته (تعریف عملی: حداقل یک attempt غیر not_entered)
- Accuracy: correct / (correct+wrong) روی attemptهای معتبر
- Volume: تعداد attempt یا دقیقه مطالعه — جدا گزارش شود
- هرگز یک عدد «پیشرفت کلی» اجباری جایگزین این سه نشود

## ۸.۶ ظرفیت
```
capacity ≈ f(free_blocks, school, classes, recent_completion_rate, state)
```
- School override همان روز را بازمحاسبه می‌کند
- Activity زمان را اشغال می‌کند ولی failure مطالعه نیست

## ۸.۷ Planner و Override
- تولید هفته پیشنهاد است
- ویرایش دستی همیشه برنده است
- generate مجدد نباید taskهای manual قفل‌شده را بدون اجازه پاک کند
- Recovery: پخش کارهای عقب‌افتاده؛ نه انتقال همه به فردا

## ۸.۸ Taught
- taught از parent به child قابل cascade
- parent می‌تواند indeterminate باشد
- practice روی taught=false فقط با تأیید صریح

## ۸.۹ پاداش
- streak فقط با فعالیت مطالعاتی معتبر روز
- Habit advice اگر data_days < 30 → نمایش داده نشود
- سکه اختیاری؛ پیش‌فرض می‌تواند خاموش باشد

## ۸.۱۰ Explain
هر recommendation ذخیره‌شده حداقل یک reason code قابل ترجمه فارسی دارد.
