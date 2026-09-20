"""Academic Knowledge (Books & Import) — Pydantic v2 schemas (doc 06, doc 09).

Import payload = doc 09 §9.1. دو حالت:
- A) TOC-only: questions غایب یا [] در هر سطحی → کاملاً معتبر
- B) با سوال: number و answer الزامی (بررسی Persian در domain.validate_book_payload)

عنوان‌ها عمداً `str | None` هستند تا پیام‌های خطای فارسی دقیق از domain بیاید
(نه 422 عمومی Pydantic).
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

BlockType = Literal["topic", "mixed", "chapter_exam", "checkup", "konkur", "other"]


class QuestionIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int | None = None
    answer: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    importance: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)


class TopicIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    block_type: BlockType | None = None
    subtopics: list["TopicIn"] = Field(default_factory=list)
    questions: list[QuestionIn] = Field(default_factory=list)


class ChapterIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    block_type: BlockType | None = None
    topics: list[TopicIn] = Field(default_factory=list)
    # انعطاف ورودی: subtopics در سطح فصل هم پذیرفته می‌شود (معادل topics)
    subtopics: list[TopicIn] = Field(default_factory=list)
    questions: list[QuestionIn] = Field(default_factory=list)


class BookImportRequest(BaseModel):
    """POST /resources/import-book — TOC-only مجاز است (doc 08 §8.3.1)."""

    model_config = ConfigDict(extra="ignore")

    title: str | None = None
    publisher: str | None = None
    subject: str | None = None
    chapters: list[ChapterIn] = Field(default_factory=list)
    # موضوعات بدون فصل هم مجازاند (انعطاف ورودی)
    topics: list[TopicIn] = Field(default_factory=list)
    # duplicate (title+publisher) → 409؛ با replace=true همان فایل جایگزین می‌شود
    replace: bool = False


class ResourceCounts(BaseModel):
    chapters: int = 0
    topics: int = 0
    questions: int = 0


class ResourceOut(BaseModel):
    id: str
    title: str
    publisher: str
    subject: str | None = None
    counts: ResourceCounts
    created_at: str


class ImportResultOut(BaseModel):
    resource: ResourceOut
    replaced: bool = False


class TreeNodeOut(BaseModel):
    id: str
    title: str
    block_type: BlockType
    block_type_fa: str
    is_structural: bool
    question_count: int
    taught: bool
    taught_state: Literal["all", "none", "partial"]
    children: list["TreeNodeOut"] = Field(default_factory=list)


class TreeOut(BaseModel):
    resource: ResourceOut
    tree: list[TreeNodeOut]
