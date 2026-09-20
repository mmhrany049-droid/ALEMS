"""Backup & Restore — SQLAlchemy 2 models.

دستی/خودکار، AES اختیاری، بدون از دست رفتن داده (doc 04, doc 06 §Backup, AT V2-S01/S02)

فیلد می‌شود در: فاز ۸
PK: UUID رشته‌ای (doc 05). نرمال‌سازی و ایندکس‌های حیاتی طبق doc 05.
"""
from app.db.base import Base  # noqa: F401 — tables register here in the phase above
