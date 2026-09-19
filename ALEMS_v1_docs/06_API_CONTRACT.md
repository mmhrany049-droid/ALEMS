# ۶. قرارداد API (API Contract) — نسخه ۱

Base URL نسخه ۱: `/api/v1`

تمام پاسخ‌ها به صورت JSON و با ساختار استاندارد:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": { ... }
}
```

در صورت خطا:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "پیام فارسی خوانا",
    "details": { ... }
  }
}
```

---

## ۶.۱ احراز هویت

### POST /auth/register
ثبت کاربر جدید

### POST /auth/login
ورود و دریافت توکن/نشست

### POST /auth/logout
خروج

### GET /auth/me
اطلاعات کاربر جاری

---

## ۶.۲ پروفایل و وضعیت

### GET /students/me
### PUT /students/me
### POST /students/me/state
### GET /students/me/state?from=&to=

---

## ۶.۳ ساختار آموزشی

### GET /subjects
### GET /subjects/{id}/chapters
### GET /chapters/{id}/topics

### POST /resources/import-book
بدنه: فایل JSON کتاب تست

### GET /resources
### GET /resources/{id}/questions

---

## ۶.۴ فعالیت و تست

### POST /activities
ثبت فعالیت مطالعه یا تست

### POST /test-records
ثبت نتیجه یک یا چند سوال

```json
{
  "records": [
    {
      "question_id": "...",
      "result": "correct|wrong|blank",
      "duration_seconds": 45,
      "marks": ["important", "hard"],
      "error_type": "careless"
    }
  ]
}
```

### GET /test-records?from=&to=&subject_id=

### POST /questions/{id}/marks
### DELETE /questions/{id}/marks/{mark_type}

---

## ۶.۵ مرور

### GET /reviews/queue
لیست مرور امروز و آینده

### POST /reviews/{id}/complete
علامت‌گذاری مرور انجام‌شده

### POST /reviews/rebuild
بازسازی صف مرور بر اساس قوانین

---

## ۶.۶ اهداف و برنامه‌ریزی

### GET /goals
### POST /goals
### PUT /goals/{id}
### DELETE /goals/{id}

### GET /time-blocks
### PUT /time-blocks

### GET /plans?date=
### PUT /plans/{date}
### POST /plans/generate-week

---

## ۶.۷ آزمون

### POST /exams
### GET /exams
### GET /exams/{id}
### POST /exams/{id}/start
### POST /exams/{id}/submit
### GET /exams/{id}/result

---

## ۶.۸ تحلیل و گزارش

### GET /analytics/overview?from=&to=
### GET /analytics/by-subject
### GET /analytics/by-topic
### GET /analytics/difficulty
### GET /analytics/mistake-types

### GET /reports/daily?date=
### GET /reports/weekly?week_start=
### GET /reports/monthly?year=&month=

### GET /export/pdf?type=weekly&week_start=
### GET /export/excel?type=...
### GET /export/json

---

## ۶.۹ پشتیبان‌گیری

### POST /backup/create
### GET /backup/list
### POST /backup/restore
### GET /backup/download/{id}

---

## ۶.۱۰ تنظیمات

### GET /settings
### PUT /settings

---

## ۶.۱۱ نکات مهم برای پیاده‌سازی

1. تمام endpointهای حساس نیاز به احراز هویت دارند.
2. تاریخ‌ها در query به صورت شمسی یا میلادی قابل قبول باشند (ترجیحاً میلادی در API و تبدیل در UI).
3. Pagination برای لیست‌های طولانی الزامی است (`page`, `page_size`).
4. فیلترهای تاریخ باید inclusive باشند.
5. خطاهای اعتبارسنجی باید پیام فارسی واضح برگردانند.
