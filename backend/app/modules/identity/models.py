"""مدل‌های ماژول هویت — users و sessions."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import UUID, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base, TimestampMixin, UUIDPk

ROLES = ("student", "admin")


class User(Base, UUIDPk, TimestampMixin):
    """کاربر سیستم — دانش‌آموز یا مدیر."""

    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(String(16), default="student")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class SessionToken(Base, UUIDPk):
    """نشست‌های فعال برای امکان خروج (لغو توکن)."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_jti: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
