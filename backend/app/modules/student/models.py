"""Student Profile, State & Taught Topics — SQLAlchemy 2 models.

پروفایل تحصیلی (پایه/رشته/هدف)، check-in + ابعاد state، تدریس‌شده‌ها با cascade (doc 08 §8.8)

فیلد می‌شود در: فاز ۱
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
