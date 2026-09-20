"""Exam Center — Pydantic v2 schemas (doc 06 §Exam، doc 12 §12.2)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ExamIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str = Field(min_length=1, max_length=200)
    kind: Literal["mock", "school_subject", "free"] = "mock"
    scheduled_date: str | None = Field(default=None, max_length=20)
    planned_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    subjects: list[str] = Field(default_factory=list, max_length=30)
    planned_topic_ids: list[str] = Field(default_factory=list, max_length=200)
    resource_id: str | None = Field(default=None, max_length=36)
    note: str | None = Field(default=None, max_length=2000)


class ExamUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    scheduled_date: str | None = Field(default=None, max_length=20)
    planned_duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    subjects: list[str] | None = Field(default=None, max_length=30)
    planned_topic_ids: list[str] | None = Field(default=None, max_length=200)
    resource_id: str | None = Field(default=None, max_length=36)
    note: str | None = Field(default=None, max_length=2000)
    status: Literal["planned", "cancelled"] | None = None


class ExamSubmitIn(BaseModel):
    """نتیجه آزمون — یا sessionهای تست (خودکار) یا شمارش دستی (امتحان مدرسه)."""

    model_config = ConfigDict(extra="ignore")

    session_ids: list[str] = Field(default_factory=list, max_length=20)
    total_count: int | None = Field(default=None, ge=0, le=2000)
    correct_count: int | None = Field(default=None, ge=0, le=2000)
    wrong_count: int | None = Field(default=None, ge=0, le=2000)
    unanswered_count: int | None = Field(default=None, ge=0, le=2000)
    not_entered_count: int | None = Field(default=None, ge=0, le=2000)
    actual_duration_minutes: int | None = Field(default=None, ge=0, le=1440)
