"""Identity & Session & Permission — SQLAlchemy 2 models.

ثبت‌نام/ورود با bcrypt، JWT، نقش‌های student/advisor/parent/admin (doc 04, doc 06 §Auth)

فیلد می‌شود در: فاز ۱
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
