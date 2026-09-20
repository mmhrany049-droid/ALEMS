# ۱۲. تحلیل، آزمون و اهداف — نسخه ۲

## ۱۲.۱ Analytics
همیشه سه بلوک جدا در overview:
1. Coverage
2. Accuracy
3. Volume

ابعاد برش: subject, chapter, topic, difficulty, error_type, time_bucket

## ۱۲.۲ Exam Center
انواع: mock | school_subject | free  
وضعیت: planned | in_progress | finished | cancelled  

Mock:
- subjects[]
- planned_topic_ids[]
- actual_topic_ids[] (بعد از اجرا)
- duration planned/actual
- scoring snapshot

## ۱۲.۳ Goals
types: long | quarterly | monthly | weekly  
Quarterly تجزیه اختیاری به milestones.

## ۱۲.۴ Konkur target tracker (نمایشی)
- target_rank یا target_major از پروفایل
- نمایش فاصله کیفی بر اساس accuracy/coverage اخیر (بدون ادعای رتبه دقیق علمی)

## ۱۲.۵ Report & Export
- daily / weekly / monthly
- PDF RTL فارسی
- Excel
- JSON کامل کاربر
