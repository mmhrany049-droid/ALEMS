"""Activity & Test Engine — SQLAlchemy 2 models (doc 05, doc 09).

doc 05:
- test_sessions: mode (timed/untimed/past), planned/actual duration, started/finished,
  source, exam_id nullable
- attempt_results (تقویت test_records): status answered|unanswered|not_entered،
  result correct|wrong|blank|unknown، answer_key_version، duration_seconds nullable
- ایندکس حیاتی: attempts (student_id, solved_at)

append-only history (doc 02 FR-T5, doc 15 V2-T05):
- هر attempt یک ردیف جدید است (بدون unique روی session+question)؛ تکرار سوال
  تاریخچه را بازنویسی نمی‌کند — scoring آخرین ردیف هر سوال را می‌بیند.
- snapshotها (question_number/topic_title/correct_answer/answer_key_version) روی
  attempt ذخیره می‌شوند و FKها SET NULL هستند → حتی اگر کتاب replace/حذف شود،
  تاریخچه attemptها دست‌نخورده می‌ماند (doc 05: «تاریخچه attempt نسخه زمان
  خودش را نگه می‌دارد»).
- استثنا (doc 09 §9.3): در past import، تکمیل بعدی «همان attempt» را به
  answered تبدیل می‌کند (نه duplicate) — توسط service با lookup انجام می‌شود.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid

_now = lambda: dt.datetime.now(dt.timezone.utc)  # noqa: E731


class TestSession(Base):
    __tablename__ = "test_sessions"
    __table_args__ = (
        CheckConstraint("mode IN ('timed','untimed','past')", name="ck_test_sessions_mode"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    mode: Mapped[str] = mapped_column(String(10), nullable=False)
    # کتاب منبع — SET NULL: حذف/replace کتاب تاریخچه جلسه را از بین نمی‌برد
    resource_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resources.id", ondelete="SET NULL"), index=True
    )
    resource_title: Mapped[str | None] = mapped_column(String(200))  # snapshot
    label: Mapped[str | None] = mapped_column(String(120))  # مثلاً «کنکور ۱۴۰۳ داخل»
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="ui", server_default="ui")
    exam_id: Mapped[str | None] = mapped_column(String(36))  # nullable — FK در فاز ۶ (exams)
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    selected_question_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    planned_duration: Mapped[int | None] = mapped_column(Integer)  # seconds (timed)
    actual_duration: Mapped[int | None] = mapped_column(Integer)  # seconds (§9.4)

    # scoring snapshot در finish (ایدمپوتنت — بعد از finish تغییر نمی‌کند)
    penalty_k: Mapped[float | None] = mapped_column(Float)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    unanswered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    not_entered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    percent_konkur: Mapped[float | None] = mapped_column(Float)
    percent_no_penalty: Mapped[float | None] = mapped_column(Float)

    started_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    finished_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class AttemptResult(Base):
    """doc 05 attempt_results — append-only (V2-T05)."""

    __tablename__ = "attempt_results"
    __table_args__ = (
        CheckConstraint("status IN ('answered','unanswered','not_entered')", name="ck_attempt_results_status"),
        CheckConstraint("result IN ('correct','wrong','blank','unknown')", name="ck_attempt_results_result"),
        CheckConstraint("duration_seconds >= 0", name="ck_attempt_results_duration_nonneg"),
        # doc 05 — ایندکس حیاتی attempts (student_id, solved_at)
        Index("ix_attempt_results_student_id_solved_at", "student_id", "solved_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("test_sessions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), index=True
    )
    topic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("topics.id", ondelete="SET NULL"))

    # snapshotها — تاریخچه نسخه زمان خودش را نگه می‌دارد حتی اگر سوال/کتاب برود
    question_number: Mapped[int | None] = mapped_column(Integer)
    topic_title: Mapped[str | None] = mapped_column(String(200))
    answer: Mapped[str | None] = mapped_column(String(40))
    correct_answer: Mapped[str | None] = mapped_column(String(40))
    answer_key_version: Mapped[int | None] = mapped_column(Integer)

    status: Mapped[str] = mapped_column(String(15), nullable=False)
    result: Mapped[str] = mapped_column(String(10), nullable=False, default="unknown", server_default="unknown")
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    solved_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class ErrorNote(Base):
    """دفترچه خطا — پایه (doc 04: Error Notebook | نوع اشتباه).

    برای هر attempt غلط یک ردیف (خودکار)؛ error_type/note توسط کاربر پر می‌شود.
    """

    __tablename__ = "error_notes"
    __table_args__ = (
        CheckConstraint(
            "error_type IN ('careless','concept','method','memory','other')",
            name="ck_error_notes_error_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    attempt_result_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("attempt_results.id", ondelete="SET NULL"), index=True, unique=True
    )
    question_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="SET NULL"), index=True
    )
    session_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("test_sessions.id", ondelete="SET NULL"), index=True
    )
    topic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("topics.id", ondelete="SET NULL"))

    # snapshotها برای نمایش حتی بعد از حذف سوال/کتاب
    book_title: Mapped[str | None] = mapped_column(String(200))
    topic_title: Mapped[str | None] = mapped_column(String(200))
    question_number: Mapped[int | None] = mapped_column(Integer)
    your_answer: Mapped[str | None] = mapped_column(String(40))
    correct_answer: Mapped[str | None] = mapped_column(String(40))

    error_type: Mapped[str | None] = mapped_column(String(20))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)


class QuestionMark(Base):
    """تیک‌ها (doc 04 Question Marking, doc 08 §8.4) — review/important/hard.

    ورودی صف مرور: marks ∈ {review, important, hard} (doc 10 §10.1).
    یکتایی (student_id, question_id) — upsert، نه duplicate.
    """

    __tablename__ = "question_marks"
    __table_args__ = (
        UniqueConstraint("student_id", "question_id", name="uq_question_marks_student_id_question_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    important: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    hard: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
