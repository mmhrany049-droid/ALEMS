# ۱۰. مرور و یادگیری — نسخه ۲

## ۱۰.۱ صف مرور
منابع ورود:
- result=wrong
- marks ∈ {review, important, hard}
- blank اگر settings.include_blank_in_review

خروج:
- complete → scheduled بعدی طبق چرخه
- postpone → تاریخ جابه‌جا، status pending

## ۱۰.۲ چرخه فاصله
intervals = settings.review_intervals پیش‌فرض [1,3,7,14] روز  
پس از اتمام چرخه → absorbed (برنمی‌گردد مگر غلط جدید)

## ۱۰.۳ خوشه‌ای
1. گروه‌بندی صف بر اساس topic/chapter
2. اولویت با critical و سررسید گذشته
3. پیشنهاد روزانه ≤ max_daily_review (۲۵)
4. اگر خوشه ≥ min_cluster (۸) ترجیح با هم

## ۱۰.۴ Learning State (سبک ولی اجباری)
برای هر (student, topic) محاسبه و ذخیره:
- coverage_score 0..1
- accuracy_score 0..1
- repeated_error_score 0..1
- recency_score 0..1
- exam_readiness 0..1
- confidence 0..1 (بر اساس تعداد evidence)

فرمول دقیق عددی در کد باید از توابع domain قابل‌تست بیاید؛ hard-code پراکنده ممنوع.

## ۱۰.۵ Weakness
ضعف = ترکیب accuracy پایین + repeated_error بالا + coverage ناکافی  
نه فقط «آخرین تست غلط بود».

## ۱۰.۶ Intervention types
`read_lesson | review | easy_practice | medium_practice | hard_practice | mixed_practice | timed_quiz | error_review`

Recommendation حداقل type + topic_id + reason برمی‌گرداند.
