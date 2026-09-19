"""مدل‌های ماژول دانش آموزشی — subjects, chapters, topics, resources, questions."""
from __future__ import annotations

import uuid

from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text, UniqueConstraint, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base, TimestampMixin, UUIDPk

RESOURCE_TYPES = ("book_test", "textbook", "note", "class", "video")
DIFFICULTIES = ("easy", "medium", "hard")
# مقادیر None برای «بدون سطح سختی» مجاز است — در تحلیل سختی نادیده گرفته می‌شود.


class Subject(Base, UUIDPk):
    """درس — رشته → پایه → درس."""

    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(64))
    field: Mapped[str] = mapped_column(String(32), index=True)
    grade: Mapped[str] = mapped_column(String(32), index=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    chapters: Mapped[list["Chapter"]] = relationship(back_populates="subject", cascade="all, delete-orphan")


class Chapter(Base, UUIDPk):
    """فصل یک درس."""

    __tablename__ = "chapters"

    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(128))
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    subject: Mapped[Subject] = relationship(back_populates="chapters")
    topics: Mapped[list["Topic"]] = relationship(back_populates="chapter", cascade="all, delete-orphan")


class Topic(Base, UUIDPk):
    """مبحث (و زیرمبحث با parent_id)."""

    __tablename__ = "topics"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(128))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    chapter: Mapped[Chapter] = relationship(back_populates="topics")


class Resource(Base, UUIDPk, TimestampMixin):
    """منبع — کتاب تست، کتاب درسی، جزوه، کلاس، ویدئو."""

    __tablename__ = "resources"

    title: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(32), default="book_test")
    subject_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="SET NULL"), nullable=True
    )
    publisher: Mapped[str | None] = mapped_column(String(120), nullable=True)
    resource_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    questions: Mapped[list["Question"]] = relationship(back_populates="resource", cascade="all, delete-orphan")


class Question(Base, UUIDPk, TimestampMixin):
    """سوال بانک سوال."""

    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_resource_topic", "resource_id", "topic_id"),
    )

    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="CASCADE"), index=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("topics.id", ondelete="RESTRICT"), index=True
    )
    number: Mapped[str] = mapped_column(String(32))
    correct_answer: Mapped[str] = mapped_column(String(16))
    difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)  # easy/medium/hard یا NULL
    importance: Mapped[int] = mapped_column(Integer, default=1)  # ۱ تا ۵
    tags: Mapped[list] = mapped_column(JSON, default=list)
    extra: Mapped[dict] = mapped_column(JSON, default=dict)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    resource: Mapped[Resource] = relationship(back_populates="questions")
    topic: Mapped[Topic] = relationship()
