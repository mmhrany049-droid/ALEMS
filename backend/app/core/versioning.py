"""Version Management — app version + schema version (doc 04 Foundation).

- APP_VERSION: product version (docs 2.0.0)
- SCHEMA_VERSION: database schema major (doc 17: schema_version -> 2.x)
- app_metadata table (migration 0001) stores per-key version info in DB
"""
from __future__ import annotations

import datetime as dt
import logging

from sqlalchemy import DateTime, String, Text, select, update
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

logger = logging.getLogger("alems.versioning")

APP_VERSION = "2.0.0"
SCHEMA_VERSION = "2.0.0"

META_KEY_APP = "app_version"
META_KEY_SCHEMA = "schema_version"


class AppMetadata(Base):
    __tablename__ = "app_metadata"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.timezone.utc),
    )


def set_meta_value(db, key: str, value: str) -> None:
    stmt = select(AppMetadata).where(AppMetadata.key == key)
    row = db.execute(stmt).scalar_one_or_none()
    now = dt.datetime.now(dt.timezone.utc)
    if row is None:
        db.add(AppMetadata(key=key, value=value, updated_at=now))
    else:
        db.execute(
            update(AppMetadata).where(AppMetadata.key == key).values(value=value, updated_at=now)
        )
    db.flush()


def get_meta_value(db, key: str, default: str | None = None) -> str | None:
    stmt = select(AppMetadata).where(AppMetadata.key == key)
    row = db.execute(stmt).scalar_one_or_none()
    return row.value if row is not None else default


def init_meta(db) -> None:
    """Record app + schema versions on first run (idempotent)."""
    set_meta_value(db, META_KEY_APP, APP_VERSION)
    set_meta_value(db, META_KEY_SCHEMA, SCHEMA_VERSION)


def schema_version_from_alembic(db) -> str:
    """Read alembic_version table directly (works for SQLite and PostgreSQL)."""
    try:
        from sqlalchemy import text

        row = db.execute(text("SELECT version_num FROM alembic_version")).first()
        return row[0] if row else "unknown"
    except Exception:  # pragma: no cover
        logger.exception("could not read alembic_version")
        return "unknown"
