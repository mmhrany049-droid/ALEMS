"""مدل‌های ماژول آزمون — exams, exam_questions, exam_results, exam_answers."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, UUIDPk
from app.modules.academic.models import Question

EXAM_TYPES = ("mock", "subject")       # آزمون آزمایشی / امتحان
EXAM_STATUSES = ("planned", "in_progress", "finished")


class Exam(Base, UUIDPk):
    """آزمون — آزمایشی (چند درس) یا امتحان (یک درس)."""

    __tablename__ = "exams"

    student_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(160))
    exam_type: Mapped[str] = mapped_column(String(16), default="mock")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60)
    status: Mapped[str] = mapped_column(String(16), default="planned")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    questions = relationship(
        "ExamQuestion", back_populates="exam",
        cascade="all, delete-orphan", order_by="ExamQuestion.order_index",
    )
    result: Mapped["ExamResult | None"] = relationship(
        back_populates="exam", cascade="all, delete-orphan", uselist=False
    )


class ExamQuestion(Base, UUIDPk):
    """سوالات آزمون به ترتیب."""

    __tablename__ = "exam_questions"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    exam: Mapped[Exam] = relationship(back_populates="questions")
    question: Mapped[Question] = relationship(Question)


class ExamResult(Base, UUIDPk):
    """نتیجه نمره‌دهی آزمون."""

    __tablename__ = "exam_results"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    blank_count: Mapped[int] = mapped_column(Integer, default=0)
    percent_konkur: Mapped[float | None] = mapped_column(Float, nullable=True)
    percent_no_penalty: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    finished_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exam: Mapped[Exam] = relationship(back_populates="result")


class ExamAnswer(Base, UUIDPk):
    """پاسخ کاربر به هر سوال آزمون."""

    __tablename__ = "exam_answers"
    __table_args__ = (
        UniqueConstraint("exam_id", "question_id", name="uq_exam_answer"),
        Index("ix_exam_answers_exam", "exam_id"),
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    result: Mapped[str] = mapped_column(String(8))
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
