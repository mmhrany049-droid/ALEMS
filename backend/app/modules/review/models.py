"""Review & Learning — SQLAlchemy 2 models (doc 05, doc 10).

doc 05:
- learning_states: student_id, topic_id, coverage, accuracy, retention_est,
  recency_score, repeated_error_score, exam_readiness, confidence, updated_at
- ایندکس حیاتی: review_queue (student_id, status, scheduled_date) و
  learning_states (student_id, topic_id)
- یکتایی: یک آیتم صف به ازای (student, question) — rebuild هرگز duplicate نمی‌سازد
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
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid

_now = lambda: dt.datetime.now(dt.timezone.utc)  # noqa: E731


class ReviewItem(Base):
    """صف مرور — ورودی: wrong / marks / blank-اختیاری (doc 10 §10.1، doc 08 §8.4)."""

    __tablename__ = "review_queue"
    __table_args__ = (
        UniqueConstraint("student_id", "question_id", name="uq_review_queue_student_id_question_id"),
        CheckConstraint(
            "source IN ('wrong','blank','mark_review','mark_important','mark_hard')",
            name="ck_review_queue_source",
        ),
        CheckConstraint("status IN ('pending','scheduled','absorbed')", name="ck_review_queue_status"),
        # doc 05 — ایندکس حیاتی
        Index("ix_review_queue_student_id_status_scheduled_date", "student_id", "status", "scheduled_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("topics.id", ondelete="SET NULL"))

    # snapshotها — نمایش حتی اگر سوال/موضوع بعداً حذف شود
    question_number: Mapped[int | None] = mapped_column(Integer)
    topic_title: Mapped[str | None] = mapped_column(String(200))
    book_title: Mapped[str | None] = mapped_column(String(200))

    source: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="pending", server_default="pending")
    critical: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    cycle_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    scheduled_date: Mapped[dt.date | None] = mapped_column(Date, index=True)
    last_reviewed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)


class LearningState(Base):
    """doc 10 §10.4 — به ازای هر (student, topic)؛ فرمول‌ها در review.domain."""

    __tablename__ = "learning_states"
    __table_args__ = (
        UniqueConstraint("student_id", "topic_id", name="uq_learning_states_student_id_topic_id"),
        Index("ix_learning_states_student_id_topic_id", "student_id", "topic_id"),  # doc 05 حیاتی
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )

    coverage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    retention_est: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    recency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    repeated_error_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    exam_readiness: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    weakness: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    # شمارش‌های شاهد (evidence) — برای UI و ضعف‌یابی
    total_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    attempted_questions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
