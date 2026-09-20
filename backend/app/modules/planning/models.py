"""Planning & Capacity & Today Hub — SQLAlchemy 2 models.

تقویم شمسی، اهداف، time blocks، ظرفیت واقعی، generate-week (pipeline ثابت)، Today Hub، priority، recommendation، recovery، manual override (doc 11)

فیلد می‌شود در: فاز ۵
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
