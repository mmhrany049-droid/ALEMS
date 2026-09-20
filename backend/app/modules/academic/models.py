"""Academic Knowledge (Books & Import) — SQLAlchemy 2 models (doc 05, doc 09).

doc 05:
- resources: کتاب/منبع (per student — کتابخانه شخصی)
- topics.block_type: topic|mixed|chapter_exam|checkup|konkur|other
- topics.is_structural: bool (گره فقط‌ساختار: فصل‌ها و والدینِ بدون سوال)
- questions + answer_keys نسخه‌دار (phase 2: version=1; موتور تست فاز ۳)
- index حیاتی: topics (resource_id, block_type)
- UUID string PK یکدست

TOC-only: هیچ سطحی question اجباری ندارد (doc 08 §8.3) — schema هم
هیچ NOT NULL روی questions ندارد.
"""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, new_uuid
from app.modules.academic.domain import BLOCK_TYPES

_now = lambda: dt.datetime.now(dt.timezone.utc)  # noqa: E731


class Resource(Base):
    """کتاب / منبع درسی. یکتایی (student_id, title, publisher) → duplicate = 409 (doc 08 §8.3.5)."""

    __tablename__ = "resources"
    __table_args__ = (
        UniqueConstraint("student_id", "title", "publisher", name="uq_resources_student_title_publisher"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    student_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # publisher NOT NULL با default '' → یکتایی حتی وقتی ناشر غایب است (SQLite NULL-in-unique)
    publisher: Mapped[str] = mapped_column(String(120), nullable=False, default="", server_default="")
    subject: Mapped[str | None] = mapped_column(String(80))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)


class Topic(Base):
    """گره درخت کتاب: فصل (is_structural) / موضوع / زیرموضوع (parent_id)."""

    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint(
            "block_type IN ('topic','mixed','chapter_exam','checkup','konkur','other')",
            name="ck_topics_block_type",
        ),
        Index("ix_topics_resource_id_block_type", "resource_id", "block_type"),  # doc 05
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    resource_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resources.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("topics.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    block_type: Mapped[str] = mapped_column(String(20), nullable=False, default="topic", server_default="topic")
    is_structural: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class Question(Base):
    """سوال — اختیاری در import (TOC-only). اگر هست: number و answer الزامی (domain)."""

    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("topic_id", "number", name="uq_questions_topic_id_number"),
        CheckConstraint("difficulty BETWEEN 1 AND 5", name="ck_questions_difficulty_range"),
        CheckConstraint("importance BETWEEN 1 AND 5", name="ck_questions_importance_range"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty: Mapped[int | None] = mapped_column(Integer)
    importance: Mapped[int | None] = mapped_column(Integer)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)


class AnswerKey(Base):
    """doc 05 — کلید پاسخ نسخه‌دار؛ فاز ۲ نسخه ۱، تاریخچه در فاز ۳+.

    سوال به آخرین نسخه key برای نمره‌دهی فعلی وصل است.
    """

    __tablename__ = "answer_keys"
    __table_args__ = (UniqueConstraint("question_id", "version", name="uq_answer_keys_question_id_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("questions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    answer: Mapped[str] = mapped_column(String(20), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
