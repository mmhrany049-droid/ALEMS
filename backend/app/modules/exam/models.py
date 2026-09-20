"""Exam Center & Scoring — SQLAlchemy 2 models (doc 12 §12.2، doc 08 §8.1).

انواع: mock | school_subject | free
وضعیت: planned | in_progress | finished | cancelled
Mock: subjects[] · planned_topic_ids[] · actual_topic_ids[] (بعد از اجرا) ·
duration planned/actual · scoring snapshot (درصد کنکوری و بدون‌غلط جدا).
PK: UUID رشته‌ای (doc 05).
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class Exam(Base):
    """یک آزمون — آزمایشی/امتحان درسی/آزاد (doc 12 §12.2)."""

    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint("kind IN ('mock','school_subject','free')", name="ck_exams_kind"),
        CheckConstraint(
            "status IN ('planned','in_progress','finished','cancelled')", name="ck_exams_status"
        ),
        Index("ix_exams_student_date", "student_id", "scheduled_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False, default="mock", server_default="mock")
    status: Mapped[str] = mapped_column(
        String(12), nullable=False, default="planned", server_default="planned", index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    resource_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resources.id", ondelete="SET NULL")
    )  # برای school_subject/free — کتاب مرتبط
    scheduled_date: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    planned_duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # mock — چند درس با چند جلسه
    subjects: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    planned_topic_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    actual_topic_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    session_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    # اجرا
    actual_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    # scoring snapshot (doc 08 §8.1 — دو درصد همیشه جدا)
    scoring: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )
