"""Activity & Test Engine — Pydantic v2 schemas (doc 06 §Tests, doc 09 §9.2).

ورودی انتخاب (doc 09 §9.2): resource_id، topic_ids اختیاری، range
(from_number/to_number)، parity (any|odd|even)، count اختیاری، difficulty اختیاری.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Mode = Literal["timed", "untimed"]  # past فقط از راه past-import ساخته می‌شود
Parity = Literal["any", "odd", "even"]
RecordStatus = Literal["answered", "unanswered"]  # not_entered مخصوص past-import است
PastStatus = Literal["answered", "unanswered", "not_entered"]
Result = Literal["correct", "wrong", "blank", "unknown"]
ErrorType = Literal["careless", "concept", "method", "memory", "other"]


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    mode: Mode = "untimed"
    resource_id: str
    topic_ids: list[str] = Field(default_factory=list)
    from_number: int | None = Field(default=None, ge=1)
    to_number: int | None = Field(default=None, ge=1)
    parity: Parity = "any"
    count: int | None = Field(default=None, ge=1)
    difficulty: int | None = Field(default=None, ge=1, le=5)
    planned_duration: int | None = Field(default=None, ge=1)  # seconds (timed)
    label: str | None = Field(default=None, max_length=120)


class RecordIn(BaseModel):
    """یک رکورد ثبت تست سریع — question_id یا number (داخل انتخاب جلسه)."""

    model_config = ConfigDict(extra="ignore")

    question_id: str | None = None
    number: int | None = None
    status: RecordStatus = "answered"
    result: Result | None = None  # صریح → برنده؛ وگرنه از answer/key استنتاج می‌شود
    answer: str | None = Field(default=None, max_length=40)
    duration_seconds: int | None = Field(default=None, ge=0)


class RecordsIn(BaseModel):
    items: list[RecordIn] = Field(min_length=1)


class FinishIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    # §9.4 — untimed: بعد از finish مدت را بپرس (UI)؛ ثانیه
    actual_duration: int | None = Field(default=None, ge=0)


class PastItemIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    number: int
    status: PastStatus = "not_entered"
    answer: str | None = Field(default=None, max_length=40)
    result: Result | None = None
    correct_answer: str | None = Field(default=None, max_length=40)  # کلید → AnswerKey نسخه‌دار
    difficulty: int | None = Field(default=None, ge=1, le=5)
    duration_seconds: int | None = Field(default=None, ge=0)


class PastImportIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resource_id: str
    topic_id: str
    label: str | None = Field(default=None, max_length=120)
    items: list[PastItemIn] = Field(min_length=1)


class ErrorNoteUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    error_type: ErrorType | None = None
    note: str | None = Field(default=None, max_length=1000)
