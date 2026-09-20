"""Student — Pydantic v2 schemas (doc 06 §Student, doc 13 §13.6)."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

Dim = int  # 1..5 scale (doc 13 §13.6: 0..1 or 1..5 — UI uses 1..5)


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    grade: str | None
    track: str | None
    target: str | None


class StudentProfileUpdate(BaseModel):
    grade: str | None = Field(default=None, max_length=20)
    track: str | None = Field(default=None, max_length=40)
    target: str | None = Field(default=None, max_length=80)


class CheckinRequest(BaseModel):
    energy: Dim = Field(ge=1, le=5)
    focus: Dim = Field(ge=1, le=5)
    motivation: Dim = Field(ge=1, le=5)
    stress: Dim = Field(ge=1, le=5)
    fatigue: Dim = Field(ge=1, le=5)


class CheckinOut(BaseModel):
    date: dt.date
    date_jalali: str
    energy: int
    focus: int
    motivation: int
    stress: int
    fatigue: int
    updated_at: dt.datetime


class StateOut(BaseModel):
    """GET /students/me/state — self-reported state (doc 13 §13.6)."""

    today: CheckinOut | None
    last: CheckinOut | None
    data_days: int  # distinct days with check-in (habit advice needs 30, doc 13 §13.4)


class TaughtTopicIn(BaseModel):
    topic_id: str = Field(min_length=1, max_length=36)
    taught: bool


class TaughtTopicsUpdate(BaseModel):
    items: list[TaughtTopicIn] = Field(min_length=1)


class TaughtTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic_id: str
    taught: bool
    updated_at: dt.datetime
