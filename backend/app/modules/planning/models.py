"""Planning & Capacity & Today Hub — SQLAlchemy 2 models (doc 05، doc 11).

جداول: goals · time_blocks · capacity_snapshots · plan_tasks · plan_runs (pipeline
لاگ‌شده — doc 11.3) · priority_snapshots · recommendations (doc 05).
PK: UUID رشته‌ای (doc 05).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
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


class Goal(Base):
    """اهداف بلند/ماه/هفته (doc 04 Goals، doc 06 GET/POST /goals)."""

    __tablename__ = "goals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="week")  # long|month|week
    target_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (CheckConstraint("kind IN ('long','month','week')", name="ck_goals_kind"),)


class TimeBlock(Base):
    """time blocks روز — مدرسه/کلاس/آزاد (doc 11.2). school-override → source='override'."""

    __tablename__ = "time_blocks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)  # school|class|free
    start_minutes: Mapped[int] = mapped_column(Integer, nullable=False)  # دقیقه از نیمه‌شب
    end_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="schedule")  # schedule|override
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    __table_args__ = (
        CheckConstraint("kind IN ('school','class','free')", name="ck_time_blocks_kind"),
        CheckConstraint("source IN ('schedule','override')", name="ck_time_blocks_source"),
        CheckConstraint("start_minutes >= 0 AND start_minutes < 1440", name="ck_time_blocks_start_range"),
        CheckConstraint("end_minutes > start_minutes AND end_minutes <= 1440", name="ck_time_blocks_end_range"),
        Index("ix_time_blocks_student_id_date", "student_id", "date"),
    )


class CapacitySnapshot(Base):
    """doc 05 capacity_snapshots — source: computed|override (override همان روز را بازمحاسبه می‌کند، doc 08 §8.6)."""

    __tablename__ = "capacity_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    school_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    class_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_study_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_capacity_tasks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    suggested_session_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="computed")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_capacity_snapshots_student_id_date"),
        CheckConstraint("source IN ('computed','override')", name="ck_capacity_snapshots_source"),
    )


class PlanTask(Base):
    """یک کار برنامه روز.

    locked=True → در regenerate حفظ می‌شود (doc 11.4، V2-P03).
    source: generated (پیشنهاد planner) | manual (ویرایش کاربر) | recovered (جبران).
    """

    __tablename__ = "plan_tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    week_start: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    kind: Mapped[str] = mapped_column(String(10), nullable=False, default="study")  # study|test|review|goal
    topic_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("topics.id", ondelete="SET NULL"), nullable=True
    )
    topic_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    book_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # تعداد سوال/آیتم
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")  # pending|done|skipped
    locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    source: Mapped[str] = mapped_column(String(10), nullable=False, default="generated")
    reason_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    __table_args__ = (
        CheckConstraint("kind IN ('study','test','review','goal')", name="ck_plan_tasks_kind"),
        CheckConstraint("status IN ('pending','done','skipped')", name="ck_plan_tasks_status"),
        CheckConstraint(
            "source IN ('generated','manual','recovered')", name="ck_plan_tasks_source"
        ),
        CheckConstraint("minutes > 0", name="ck_plan_tasks_minutes"),
        Index("ix_plan_tasks_student_id_date", "student_id", "date"),
        Index("ix_plan_tasks_student_id_week_start", "student_id", "week_start"),
    )


class PlanRun(Base):
    """اجرای pipeline تولید هفته — steps لاگ‌شده (doc 11.3: ترتیب ثابت باید لاگ شود)."""

    __tablename__ = "plan_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    week_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="ok")  # ok|partial
    steps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    kept_locked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    removed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class PrioritySnapshot(Base):
    """doc 05 priority_snapshots — چه مباحثی این هفته مهم‌اند (doc 11.6)."""

    __tablename__ = "priority_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    week_start: Mapped[dt.date] = mapped_column(Date, nullable=False)
    items: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    __table_args__ = (
        UniqueConstraint("student_id", "week_start", name="uq_priority_snapshots_student_id_week_start"),
    )


class Recommendation(Base):
    """doc 05 recommendations — پیشنهاد امروز با reasons (doc 08 §8.10 ≥ یک reason code)."""

    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reasons: Mapped[list] = mapped_column(JSON, nullable=False, default=list)  # [{code, fa}]
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="suggested")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    __table_args__ = (
        Index("ix_recommendations_student_id_date", "student_id", "date"),
        CheckConstraint(
            "status IN ('suggested','accepted','rejected','edited')", name="ck_recommendations_status"
        ),
    )
