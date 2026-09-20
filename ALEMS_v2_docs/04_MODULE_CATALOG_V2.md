# ۴. کاتالوگ ماژول‌ها — ALEMS نسخه ۲

علامت `[V2]` = الزامی نسخه ۲

---

## Foundation
| ماژول | مسئولیت |
|-------|---------|
| Core System `[V2]` | config، Event Bus، lifecycle |
| Database `[V2]` | SQLAlchemy، Alembic |
| File Management `[V2]` | data/backups/exports/imports |
| Backup & Restore `[V2]` | دستی، خودکار، AES |
| Version Management `[V2]` | app + schema version |
| Settings `[V2]` | سیاست‌ها بدون hard-code |

## Identity & Student
| ماژول | مسئولیت |
|-------|---------|
| User Identity `[V2]` | ثبت‌نام، ورود، bcrypt |
| Session `[V2]` | JWT |
| Permission `[V2]` | student / advisor / parent / admin |
| Student Profile `[V2]` | پایه، رشته، هدف |
| Student State `[V2]` | check-in + state dimensions |
| Taught Topics `[V2]` | تدریس‌شده آبشاری |

## Academic Knowledge
| ماژول | مسئولیت |
|-------|---------|
| Knowledge Base `[V2]` | درخت دروس |
| Resource & Book `[V2]` | منابع و کتاب |
| Book Import `[V2]` | **TOC-only و کامل** |
| Question Bank `[V2]` | سوال + answer key نسخه‌دار |
| Classification `[V2]` | سختی، تگ، اهمیت |
| Block Type `[V2]` | topic / mixed / exam / checkup / konkur |

## Activity & Test
| ماژول | مسئولیت |
|-------|---------|
| Learning Activity `[V2]` | مطالعه/کلاس/... |
| Test Record `[V2]` | attempt append-only |
| Test Engine `[V2]` | range، parity، timed |
| Time Tracking `[V2]` | مدت واقعی و میانگین |
| Past Import `[V2]` | نتایج قدیمی + NOT_ENTERED |
| Question Marking `[V2]` | تیک‌ها |
| Error Notebook `[V2]` | نوع اشتباه |

## Review & Learning
| ماژول | مسئولیت |
|-------|---------|
| Review Queue `[V2]` | صف |
| Spaced Cycle `[V2]` | ۱-۳-۷-۱۴ |
| Cluster Review `[V2]` | خوشه‌ای/تصادفی |
| Learning State `[V2]` | متریک‌های چندبعدی |
| Weakness Detector `[V2]` | ضعف عملی |
| Intervention `[V2]` | نوع مداخله پیشنهادی |

## Planning
| ماژول | مسئولیت |
|-------|---------|
| Calendar `[V2]` | شمسی |
| Goals `[V2]` | بلند/ماه/هفته + سه‌ماهه ساده |
| Time Blocks `[V2]` | مدرسه/کلاس/آزاد |
| Capacity `[V2]` | توان واقعی |
| Planner `[V2]` | روز/هفته |
| Today Hub `[V2]` | مرکز روز |
| Priority `[V2]` | اولویت هفته |
| Recommendation `[V2]` | پیشنهاد کار |
| Recovery `[V2]` | جبران عقب‌افتادگی |
| Manual Override `[V2]` | ویرایش کامل کاربر |

## Exam & Analytics
| ماژول | مسئولیت |
|-------|---------|
| Exam Center `[V2]` | آزمایشی و امتحان |
| Scoring `[V2]` | کنکوری / بدون غلط |
| Analytics `[V2]` | coverage/accuracy/volume |
| Visualization `[V2]` | نمودارها |
| Report `[V2]` | روزانه تا ماهانه |
| Export `[V2]` | PDF/Excel/JSON |
| Explain `[V2]` | چرا این پیشنهاد |

## Motivation
| ماژول | مسئولیت |
|-------|---------|
| Points & Streak `[V2]` | |
| Badges `[V2]` | |
| Habit Advice `[V2]` | بعد از ۳۰ روز داده |
| Procrastination Aid `[V2]` | شروع کوچک |

## Collaboration (پایه)
| ماژول | مسئولیت |
|-------|---------|
| Share Report `[V2]` | اشتراک کنترل‌شده |

## UI Shell
| ماژول | مسئولیت |
|-------|---------|
| Design System `[V2]` | توکن رنگ/فاصله/تایپ |
| Motion System `[V2]` | variants فرمر |
| Focus Mode `[V2]` | |
| Theme `[V2]` | dark/light |
