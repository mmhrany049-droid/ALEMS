"""اسکیماهای ماژول فعالیت."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.activity.models import ACTIVITY_TYPES, TEST_RESULTS


class ActivityIn(BaseModel):
    type: str = Field(description="نوع فعالیت: study/test/review/class/school")
    subject_id: uuid.UUID | None = None
    resource_id: uuid.UUID | None = None
    started_at: datetime | None = Field(None, description="زمان شروع (پیش‌فرض اکنون)")
    duration_minutes: int = Field(ge=0, le=24 * 60, description="مدت به دقیقه")
    note: str | None = Field(None, max_length=2000)

    @model_validator(mode="after")
    def check_type(self) -> "ActivityIn":
        if self.type not in ACTIVITY_TYPES:
            raise ValueError(f"نوع فعالیت نامعتبر است. مقادیر مجاز: {', '.join(ACTIVITY_TYPES)}")
        return self


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    subject_id: uuid.UUID | None
    resource_id: uuid.UUID | None
    started_at: datetime
    duration_minutes: int
    note: str | None


class TestRecordItemIn(BaseModel):
    question_id: uuid.UUID
    result: str = Field(description="نتیجه: correct/wrong/blank")
    duration_seconds: int | None = Field(None, ge=0)
    marks: list[str] = Field(default_factory=list, description="تیک‌ها: important/review/hard/mistake/tip")
    error_type: str | None = Field(None, description="نوع اشتباه — فقط برای غلط")
    solved_at: datetime | None = Field(None, description="زمان حل (پیش‌فرض اکنون)")

    @model_validator(mode="after")
    def check_result(self) -> "TestRecordItemIn":
        if self.result not in TEST_RESULTS:
            raise ValueError(f"نتیجه نامعتبر است. مقادیر مجاز: {', '.join(TEST_RESULTS)}")
        valid_marks = {"important", "review", "hard", "mistake", "tip"}
        for mark in self.marks:
            if mark not in valid_marks:
                raise ValueError(f"تیک نامعتبر است: «{mark}». مقادیر مجاز: {', '.join(sorted(valid_marks))}")
        return self


class TestRecordsIn(BaseModel):
    records: list[TestRecordItemIn] = Field(min_length=1, max_length=500)


class MarkIn(BaseModel):
    mark_type: str = Field(description="نوع تیک: important/review/hard/mistake/tip")

    @model_validator(mode="after")
    def check_mark(self) -> "MarkIn":
        from app.modules.activity.models import MARK_TYPES

        if self.mark_type not in MARK_TYPES:
            raise ValueError(f"نوع تیک نامعتبر است. مقادیر مجاز: {', '.join(MARK_TYPES)}")
        return self
