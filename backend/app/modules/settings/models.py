"""Settings — SQLAlchemy 2 models.

سیاست‌ها بدون hard-code: k جریمه کنکور، چرخه مرور [1,3,7,14]، سقف روزانه مرور، سکه (OD1) و ...

فیلد می‌شود در: فاز ۱
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
