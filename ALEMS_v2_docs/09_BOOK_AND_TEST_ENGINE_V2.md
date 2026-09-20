# ۹. کتاب و موتور تست — نسخه ۲

## ۹.۱ Book Import

### حالت A — TOC-only
```json
{
  "title": "شیمی ۲",
  "publisher": "مبتکران",
  "subject": "شیمی",
  "chapters": [
    {
      "title": "فصل ۱",
      "topics": [
        {
          "title": "الگوها و روندها",
          "block_type": "topic",
          "subtopics": [
            { "title": "جدول دوره‌ای" }
          ]
        }
      ]
    }
  ]
}
```
بدون questions کاملاً معتبر است.

### حالت B — با سوال
هر question: `number`, `answer` الزامی؛ `difficulty`, `importance`, `tags` اختیاری.

### استنتاج block_type از عنوان (اگر نیامده)
- شامل «کنکور» → konkur
- شامل «جامع» یا «آزمون فصل» → chapter_exam
- شامل «چکاپ» یا «مخلوط» → mixed یا checkup
- وگرنه topic

## ۹.۲ Test Engine

### ورودی انتخاب
- resource_id
- topic_ids اختیاری
- range: from_number, to_number
- parity: any | odd | even
- count اختیاری
- difficulty فیلتر اختیاری

### خطا
اگر بعد از فیلتر سوالی نماند:
`message`: «فقط X سوال با این شرایط وجود دارد.»

### Session
1. create session (mode)
2. add records
3. finish → scoring + events + learning state update

## ۹.۳ Past Import
- ردیفها می‌توانند status=not_entered داشته باشند
- تکمیل بعدی همان attempt را به answered تبدیل می‌کند (نه duplicate)

## ۹.۴ Time Tracking
- Untimed: پس از finish بپرسد مدت (UI) یا از timer
- ذخیره per attempt و aggregate per topic
