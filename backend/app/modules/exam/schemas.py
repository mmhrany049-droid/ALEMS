"""اسکیماهای ماژول آزمون."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.exam.models import EXAM_TYPES


class ExamCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=160, description="عنوان آزمون")
    exam_type: str = Field("mock", description="نوع: mock (آزمایشی) یا subject (امتحان)")
    scheduled_at: datetime | None = Field(None, description="زمان برگزاری (پیش‌فرض اکنون)")
    duration_minutes: int = Field(ge=1, le=24 * 60, description="مدت آزمون به دقیقه")
    question_ids: list[uuid.UUID] = Field(min_length=1, description="شناسه سوالات به ترتیب")

    @model_validator(mode="after")
    def check_type(self) -> "ExamCreateIn":
        if self.exam_type not in EXAM_TYPES:
            raise ValueError("نوع آزمون نامعتبر است. مقادیر مجاز: mock، subject")
        return self


class ExamAnswerIn(BaseModel):
    question_id: uuid.UUID
    result: str = Field(description="correct/wrong/blank")
    duration_seconds: int | None = Field(None, ge=0)


class ExamSubmitIn(BaseModel):
    answers: list[ExamAnswerIn] = Field(min_length=1, description="پاسخ‌های آزمون")


class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    exam_type: str
    scheduled_at: datetime
    duration_minutes: int
    status: str
    started_at: datetime | None
