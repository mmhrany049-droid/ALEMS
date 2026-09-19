"""مدل‌های ماژول فعالیت — activities, test_records, question_marks, error_notes, review_queue."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Date,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, UUIDPk, new_uuid

ACTIVITY_TYPES = ("study", "test", "review", "class", "school")
TEST_RESULTS = ("correct", "wrong", "blank")
MARK_TYPES = ("important", "review", "hard", "mistake", "tip")
ERROR_TYPES = ("unknown", "forgotten", "careless", "time")
REVIEW_STATUSES = ("pending", "done")


class LearningActivity(Base, UUIDPk):
    """جلسه فعالیت — مطالعه، تست‌زنی، مرور، کلاس، مدرسه."""

    __tablename__ = "learning_activities"
    __table_args__ = (Index("ix_activities_student_started", "student_id", "started_at"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    type: Mapped[str] = mapped_column(String(16))  # study/test/review/class/school
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    resource_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resources.id", ondelete="SET NULL"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)


class TestRecord(Base, UUIDPk):
    """نتیجه حل یک سوال — درست/غلط/نزده."""

    __tablename__ = "test_records"
    __table_args__ = (Index("ix_test_records_student_solved", "student_id", "solved_at"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    result: Mapped[str] = mapped_column(String(8))  # correct/wrong/blank
    solved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    activity_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("learning_activities.id", ondelete="SET NULL"), nullable=True
    )

    question = relationship("Question")
    error_note: Mapped["ErrorNote | None"] = relationship(
        back_populates="test_record", cascade="all, delete-orphan", uselist=False
    )


class QuestionMark(Base, UUIDPk):
    """تیک سوال — یک سوال می‌تواند چندین تیک همزمان داشته باشد."""

    __tablename__ = "question_marks"
    __table_args__ = (
        UniqueConstraint("student_id", "question_id", "mark_type", name="uq_question_mark"),
        Index("ix_question_marks_student_question", "student_id", "question_id"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    mark_type: Mapped[str] = mapped_column(String(16))  # important/review/hard/mistake/tip
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ErrorNote(Base, UUIDPk):
    """دفترچه خطا — نوع اشتباه برای هر غلط."""

    __tablename__ = "error_notes"

    test_record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("test_records.id", ondelete="CASCADE"), index=True
    )
    error_type: Mapped[str] = mapped_column(String(16))  # unknown/forgotten/careless/time
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    test_record: Mapped[TestRecord] = relationship(back_populates="error_note")


class ReviewItem(Base, UUIDPk):
    """آیتم صف مرور."""

    __tablename__ = "review_queue"
    __table_args__ = (Index("ix_review_queue_student_status_date", "student_id", "status", "scheduled_date"),)

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(String(16))  # wrong/blank/mark_important/mark_hard/mark_review
    priority: Mapped[int] = mapped_column(Integer, default=1)
    scheduled_date: Mapped[date] = mapped_column(Date, default=date.today)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(8), default="pending")  # pending/done
    question = relationship("Question")
