"""Student Profile / State / Taught Topics — models (doc 04, doc 05).

doc 05:
- taught_topics: id, student_id, topic_id, taught (bool), updated_at;
  یکتایی (student_id, topic_id)
- UUID string PK uniformly
Check-in date is the Tehran calendar day (doc 03 §3.5: stored UTC/ISO,
displayed Jalali) — 1:1 with the Jalali day, so streaks stay unambiguous.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid

# doc 13 §13.6 — state dimensions (self-report via check-in), scale 1..5
CHECKIN_DIMENSIONS = ("energy", "focus", "motivation", "stress", "fatigue")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    # doc 04 Student Profile: پایه، رشته، هدف
    grade: Mapped[str | None] = mapped_column(String(20))
    track: Mapped[str | None] = mapped_column(String(40))
    target: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
    )


class Checkin(Base):
    __tablename__ = "checkins"
    __table_args__ = (
        UniqueConstraint("student_id", "date", name="uq_checkins_student_id_date"),
        *[
            CheckConstraint(f"{d} BETWEEN 1 AND 5", name=f"ck_checkins_{d}_range")
            for d in CHECKIN_DIMENSIONS
        ],
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    date: Mapped[dt.date] = mapped_column(Date, nullable=False)  # Tehran calendar day
    energy: Mapped[int] = mapped_column(Integer, nullable=False)
    focus: Mapped[int] = mapped_column(Integer, nullable=False)
    motivation: Mapped[int] = mapped_column(Integer, nullable=False)
    stress: Mapped[int] = mapped_column(Integer, nullable=False)
    fatigue: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: dt.datetime.now(dt.timezone.utc)
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
    )


class TaughtTopic(Base):
    __tablename__ = "taught_topics"
    __table_args__ = (UniqueConstraint("student_id", "topic_id", name="uq_taught_topics_student_id_topic_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    # FK to academic.topics lands in phase 2 (books/topics migration)
    topic_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    taught: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: dt.datetime.now(dt.timezone.utc),
        onupdate=lambda: dt.datetime.now(dt.timezone.utc),
    )
