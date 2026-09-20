"""Motivation (Rewards & Behavior) — SQLAlchemy 2 models (doc 05، doc 13).

جداول: points_ledger (append-only) · streaks · badges (seed — OD4: ۸ تا ۱۲) ·
badge_awards (امضای دریافت یکتا per user/badge).
PK: UUID رشته‌ای (doc 05).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class PointsEntry(Base):
    """doc 13.1 — ledger append-only؛ یک ردیف به ازای هر رویداد امتیازآور.

    unique(student_id, source_event, ref_id) = امضای یکتایی — رویداد تکراری
    (مثلاً finish ایدمپوتنت یا check-in مجدد) هرگز دوباره امتیاز نمی‌گیرد.
    active_date: تاریخ شمسی ISO (روزِ فعالیت معتبر — منبع streak، doc 13.2).
    """

    __tablename__ = "points_ledger"
    __table_args__ = (
        UniqueConstraint("student_id", "source_event", "ref_id", name="uq_points_ledger_student_source_ref"),
        CheckConstraint(
            "source_event IN ('plan_task.completed','review.completed','test_session.finished','checkin.submitted')",
            name="ck_points_ledger_source_event",
        ),
        CheckConstraint("points > 0", name="ck_points_ledger_points_positive"),
        Index("ix_points_ledger_student_id_active_date", "student_id", "active_date"),  # streak/habit
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_event: Mapped[str] = mapped_column(String(40), nullable=False)
    ref_id: Mapped[str] = mapped_column(String(80), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    active_date: Mapped[str] = mapped_column(String(10), nullable=False)  # «1405/06/29»
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class StreakState(Base):
    """doc 05 streaks — وضعیت پیوستگی (کش ledger؛ همیشه از ledger قابل بازسازی)."""

    __tablename__ = "streaks"
    __table_args__ = (
        UniqueConstraint("student_id", name="uq_streaks_student_id"),
        CheckConstraint("current_streak >= 0", name="ck_streaks_current_nonneg"),
        CheckConstraint("longest_streak >= 0", name="ck_streaks_longest_nonneg"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    current_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_active_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # شمسی ISO
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class Badge(Base):
    """doc 13.3 — تعریف در seed: کد، عنوان، شرط (kind + target)."""

    __tablename__ = "badges"
    __table_args__ = (
        UniqueConstraint("code", name="uq_badges_code"),
        CheckConstraint("target > 0", name="ck_badges_target_positive"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    title_fa: Mapped[str] = mapped_column(String(120), nullable=False)
    description_fa: Mapped[str] = mapped_column(String(240), nullable=False, default="")
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # active_days|streak|reviews|sessions|exams|points|answers
    target: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class BadgeAward(Base):
    """doc 13.3 — امضای دریافت یکتا per user/badge."""

    __tablename__ = "badge_awards"
    __table_args__ = (
        UniqueConstraint("student_id", "badge_id", name="uq_badge_awards_student_badge"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    badge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("badges.id", ondelete="CASCADE"), index=True, nullable=False
    )
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    awarded_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
