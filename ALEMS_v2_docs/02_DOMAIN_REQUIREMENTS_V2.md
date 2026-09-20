# ۲. نیازمندی‌های دامنه — ALEMS نسخه ۲

## ۲.۱ مفاهیم کلیدی

| مفهوم | تعریف V2 |
|-------|----------|
| Taught | مبحث تدریس/ارائه‌شده؛ ≠ تسلط |
| Learning State | برآورد چندبعدی وضعیت یادگیری مبحث |
| Coverage | نسبت مباحث/سوالات پوشش‌داده‌شده |
| Accuracy | کیفیت پاسخ‌های داده‌شده |
| Volume | حجم کار انجام‌شده (تعداد/زمان) |
| Capacity | توان واقعی تکمیل کار، نه ساعت خالی |
| Activity | اشغال‌کننده زمان (مدرسه، کلاس، زندگی) |
| Study Task | کار مطالعاتی قابل انجام |
| NOT_ENTERED | نتیجه تاریخی هنوز وارد نشده |
| UNANSWERED | کاربر واقعاً نزده |
| Block Type | topic / mixed / chapter_exam / checkup / konkur |

## ۲.۲ نیازمندی‌های عملکردی خلاصه

### کتاب
- FR-B1: Import TOC-only بدون سوال موفق باشد
- FR-B2: Import کامل با سوال و پاسخ
- FR-B3: نوع بلوک در درخت ذخیره و نمایش داده شود
- FR-B4: اصلاح نگاشت سوال-مبحث ممکن باشد

### تست
- FR-T1: ثبت تکی/دسته‌ای
- FR-T2: Range + parity
- FR-T3: Timed/Untimed + time tracking
- FR-T4: Past import با NOT_ENTERED
- FR-T5: history append-only

### مرور
- FR-R1: صف از غلط/نزده/تیک
- FR-R2: چرخه ۱-۳-۷-۱۴
- FR-R3: خوشه‌ای + تصادفی با سقف
- FR-R4: critical برای غلط تکراری

### برنامه
- FR-P1: Today Hub
- FR-P2: ظرفیت از مدرسه/کلاس/سابقه
- FR-P3: override مدرسه
- FR-P4: manual override کامل
- FR-P5: recovery بدون dump

### تحلیل
- FR-A1: سه متریک جدا
- FR-A2: گزارش + export
- FR-A3: explain پیشنهاد

### UI
- FR-U1: طراحی جدید
- FR-U2: انیمیشن Framer Motion
- FR-U3: dark/light + focus mode

## ۲.۳ غیرعملکردی

- NFR-1: Offline قابلیت‌های اصلی
- NFR-2: ثبت تست < 300ms در حالت محلی
- NFR-3: RTL کامل
- NFR-4: پورت پیش‌فرض Backend 8010
- NFR-5: prefers-reduced-motion رعایت شود
