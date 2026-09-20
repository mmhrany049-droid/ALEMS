"""Planning & Capacity & Today Hub — Pydantic v2 schemas (doc 06 §Planning، doc 11)."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class GoalIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    kind: Literal["long", "month", "week"] = "week"
    target_date: str | None = Field(default=None, max_length=20)


class TimeBlockIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    kind: Literal["school", "class", "free"]
    start: str | int  # «HH:MM» یا دقیقه از نیمه‌شب
    end: str | int
    title: str | None = Field(default=None, max_length=120)


class TimeBlocksPut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str = Field(min_length=4, max_length=20)
    blocks: list[TimeBlockIn] = Field(default_factory=list, max_length=24)


class SchoolOverrideIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str = Field(min_length=4, max_length=20)
    school_off: bool = False
    blocks: list[TimeBlockIn] = Field(default_factory=list, max_length=12)


class PlanTaskIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = Field(default=None, max_length=36)
    title: str | None = Field(default=None, max_length=200)
    kind: Literal["study", "test", "review", "goal"] | None = None
    minutes: int | None = Field(default=None, ge=5, le=600)
    count: int | None = Field(default=None, ge=0, le=1000)
    status: Literal["pending", "done", "skipped"] | None = None
    locked: bool | None = None
    topic_id: str | None = Field(default=None, max_length=36)
    reason_code: str | None = Field(default=None, max_length=40)


class PlansPut(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tasks: list[PlanTaskIn] = Field(default_factory=list, max_length=40)


class MoveTaskIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    task_id: str = Field(min_length=1, max_length=36)
    to_date: str = Field(min_length=4, max_length=20)


class SplitTaskIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    parts: list[int] = Field(min_length=2, max_length=6)


class MergeTasksIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    task_ids: list[str] = Field(min_length=2, max_length=20)


class TaskStatusIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["pending", "done", "skipped"]


class TaskLockIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    locked: bool


class GenerateWeekIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    week_start: str | None = Field(default=None, max_length=20)


class RecoverIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str | None = Field(default=None, max_length=20)


class RecommendationRespondIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: Literal["accepted", "rejected", "edited"]
    payload: dict[str, Any] | None = None
