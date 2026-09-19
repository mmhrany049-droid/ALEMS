"""مدیریت نسخه — Version Management Module (کاتالوگ ماژول‌ها §5).

مسئولیت‌ها:
- ثبت نسخه برنامه و نسخه schema
- ثبت نسخه‌های اعمال‌شده روی پایگاه داده (جدول schema_version — سند ۵.۲)
- آمادگی برای توسعه چندساله: بررسی به‌روز بودن schema نسبت به کد

نکته: اجرای migrationها با Alembic است؛ این ماژول وضعیت را ثبت و گزارش می‌کند.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.config import settings
from app.db.session import Base


class SchemaVersion(Base):
    """نسخه‌های schema اعمال‌شده روی پایگاه داده (سند ۵.۲)."""

    __tablename__ = "schema_version"

    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    applied_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)


def ensure_schema_version_record(db: Session) -> bool:
    """ثبت نسخه جاری schema در صورت نبود — idempotent (در هر راه‌اندازی اجرا می‌شود)."""
    existing = db.get(SchemaVersion, settings.schema_version)
    if existing is not None:
        return False
    db.add(SchemaVersion(version=settings.schema_version))
    db.commit()
    return True


def schema_state(db: Session) -> dict:
    """وضعیت schema نسبت به کد — برای /health و تشخیص نیاز به migration.

    up_to_date = آخرین نسخه ثبت‌شده با نسخه مورد انتظار کد یکی است.
    """
    try:
        applied = list(db.scalars(
            select(SchemaVersion).order_by(SchemaVersion.applied_at)
        ))
    except Exception:  # noqa: BLE001 — جدول هنوز ساخته نشده (قبل از اولین migration)
        return {"recorded": False, "up_to_date": False,
                "applied_versions": [], "expected": settings.schema_version}

    applied_versions = [row.version for row in applied]
    return {
        "recorded": bool(applied_versions),
        "up_to_date": settings.schema_version in applied_versions,
        "applied_versions": applied_versions,
        "expected": settings.schema_version,
    }


def version_info() -> dict:
    """اطلاعات نسخه برنامه — منبع یگانه حقیقت نسخه‌ها (config)."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "schema_version": settings.schema_version,
        "timezone": settings.timezone,
        "language": settings.language,
    }
