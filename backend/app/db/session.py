"""پایگاه داده — Database Management Module (SQLAlchemy 2.0)."""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import datetime

from sqlalchemy import UUID, DateTime, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    """کلاس پایه همه مدل‌ها."""


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class UUIDPk:
    """کلید اصلی UUID برای همه جداول."""

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=new_uuid)


class TimestampMixin:
    """زمان‌های ساخت و آخرین به‌روزرسانی."""

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


def _make_engine() -> Engine:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):  # noqa: ANN001
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


engine = _make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """وابستگی FastAPI برای نشست دیتابیس."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
