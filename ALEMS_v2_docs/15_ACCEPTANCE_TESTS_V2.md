# ۱۵. تست‌های پذیرش — ALEMS نسخه ۲

## کتاب و Import
| ID | تست |
|----|-----|
| V2-B01 | Import TOC-only بدون questions موفق است |
| V2-B02 | topic فقط با subtopics و بدون سوال مستقیم موفق است |
| V2-B03 | سوال بدون answer رد می‌شود با پیام فارسی |
| V2-B04 | block_type از عنوان آزمون/کنکور استنتاج می‌شود |
| V2-B05 | کتاب تکراری 409 |

## تست
| ID | تست |
|----|-----|
| V2-T01 | Range + odd فقط فردها |
| V2-T02 | finish ایدمپوتنت |
| V2-T03 | past import با not_entered |
| V2-T04 | درصد کنکوری نمونه استاندارد |
| V2-T05 | history append-only برای تکرار سوال |

## مرور
| ID | تست |
|----|-----|
| V2-R01 | غلط وارد صف می‌شود |
| V2-R02 | چرخه ۱ سپس ۳ |
| V2-R03 | critical برای غلط ≥۲ |
| V2-R04 | postpone |

## برنامه
| ID | تست |
|----|-----|
| V2-P01 | Today حداقل ۵ بخش سند ۷ |
| V2-P02 | school override ظرفیت را عوض می‌کند |
| V2-P03 | task قفل‌شده بعد از regenerate می‌ماند |
| V2-P04 | recovery همه را به فردا نمی‌ریزد |

## تحلیل
| ID | تست |
|----|-----|
| V2-A01 | overview هر سه متریک را جدا دارد |
| V2-A02 | export json شامل کتاب و attempt |

## UI
| ID | تست |
|----|-----|
| V2-U01 | Framer Motion در page transition فعال |
| V2-U02 | prefers-reduced-motion حرکت را کم می‌کند |
| V2-U03 | dark mode کامل |
| V2-U04 | پورت API پیش‌فرض 8010 در پروکسی |

## Backup
| ID | تست |
|----|-----|
| V2-S01 | backup/restore دور کامل |
| V2-S02 | restore بدون confirm رد می‌شود |
