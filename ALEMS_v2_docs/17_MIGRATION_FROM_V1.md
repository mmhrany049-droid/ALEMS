# ۱۷. مهاجرت از ALEMS نسخه ۱

## اصول
- داده کاربر از بین نرود
- backup قبل از migration اجباری در راهنما
- schema_version به 2.x

## نگاشت
- test_records → attempt_results (+ status پیش‌فرض answered)
- topics بدون block_type → topic
- settings قدیمی merge با پیش‌فرض V2
- review_queue حفظ

## UI
- فرانت V2 جایگزین V1؛ API سازگار با افزونه‌های V2

## پورت
- پیش‌فرض جدید 8010؛ در README و vite proxy و scripts یکسان
