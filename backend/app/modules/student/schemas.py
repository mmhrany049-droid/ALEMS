"""اسکیماهای ماژول دانش‌آموز."""
from __future__ import annotations

import uuid
from datetime import date as _date_type
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.modules.student.models import FIELDS, GRADES


class ProfileIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120, description="نام کامل")
    grade: str = Field(description="پایه تحصیلی")
    field: str = Field(description="رشته تحصیلی")
    academic_year: str | None = Field(None, max_length=16)
    target_rank: int | None = Field(None, ge=1, le=10_000_000)
    target_major: str | None = Field(None, max_length=64)

    @model_validator(mode="after")
    def check_grade_field(self) -> "ProfileIn":
        if self.grade not in GRADES:
            raise ValueError(f"پایه باید یکی از مقادیر {', '.join(GRADES)} باشد.")
        if self.field not in FIELDS:
            raise ValueError(f"رشته باید یکی از مقادیر {', '.join(FIELDS)} باشد.")
        return self


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class StateIn(BaseModel):
    date: _date_type | None = Field(None, description="تاریخ (پیش‌فرض امروز تهران)")
    energy_level: int = Field(ge=1, le=5, description="سطح انرژی ۱ تا ۵")
    mood: str | None = Field(None, max_length=64, description="حال روحی")
    study_condition: str | None = Field(None, max_length=64, description="شرایط مطالعه")
    note: str | None = Field(None, max_length=2000, description="یادداشت")


class StateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    date: _date_type
    energy_level: int
    mood: str | None
    study_condition: str | None
    note: str | None
