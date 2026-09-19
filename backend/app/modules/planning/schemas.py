"""اسکیماهای ماژول برنامه‌ریزی."""
from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.planning.domain import validate_time_range
from app.modules.planning.models import BLOCK_TYPES, GOAL_STATUSES, GOAL_TYPES


class GoalIn(BaseModel):
    type: str = Field(description="نوع هدف: long/monthly/weekly")
    title: str = Field(min_length=1, max_length=200)
    target_value: dict | None = None
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check(self) -> "GoalIn":
        if self.type not in GOAL_TYPES:
            raise ValueError(f"نوع هدف نامعتبر است. مقادیر مجاز: {', '.join(GOAL_TYPES)}")
        if self.end_date < self.start_date:
            raise ValueError("تاریخ پایان هدف نمی‌تواند قبل از تاریخ شروع باشد.")
        return self


class GoalUpdateIn(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    target_value: dict | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = None

    @model_validator(mode="after")
    def check_status(self) -> "GoalUpdateIn":
        if self.status is not None and self.status not in GOAL_STATUSES:
            raise ValueError(f"وضعیت هدف نامعتبر است. مقادیر مجاز: {', '.join(GOAL_STATUSES)}")
        return self


class TimeBlockIn(BaseModel):
    day_of_week: int = Field(ge=0, le=6, description="۰=شنبه ... ۶=جمعه")
    start_time: str = Field(description="HH:MM")
    end_time: str = Field(description="HH:MM")
    block_type: str = Field(description="school/class/study/free")
    title: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def check(self) -> "TimeBlockIn":
        if self.block_type not in BLOCK_TYPES:
            raise ValueError(f"نوع بلوک نامعتبر است. مقادیر مجاز: {', '.join(BLOCK_TYPES)}")
        validate_time_range(self.start_time, self.end_time)
        return self


class TimeBlocksIn(BaseModel):
    blocks: list[TimeBlockIn] = Field(max_length=100)


class PlanItemIn(BaseModel):
    start: str = Field(description="HH:MM")
    end: str = Field(description="HH:MM")
    title: str = Field(min_length=1, max_length=200)
    subject: str | None = None
    type: str = "study"
    done: bool = False

    @model_validator(mode="after")
    def check_time(self) -> "PlanItemIn":
        validate_time_range(self.start, self.end)
        return self


class PlanIn(BaseModel):
    items: list[PlanItemIn] = Field(max_length=50)
    status: str | None = None

    @model_validator(mode="after")
    def check_status(self) -> "PlanIn":
        if self.status is not None and self.status not in ("draft", "active", "done"):
            raise ValueError("وضعیت برنامه نامعتبر است. مقادیر مجاز: draft، active، done")
        return self


class GenerateWeekIn(BaseModel):
    week_start: date = Field(description="تاریخ شنبه هفته (ISO)")
    goal_ids: list[uuid.UUID] = Field(default_factory=list, description="اهداف فعال در برنامه")
