"""Exam Center & Scoring — SQLAlchemy 2 models.

mock | school_subject | free؛ planned/in_progress/finished/cancelled؛ درصد کنکوری (C - k*W)/T (doc 08 §8.1, doc 12 §12.2)

فیلد می‌شود در: فاز ۶
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
