"""اسکیماهای Pydantic ماژول هویت."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=64, description="نام کاربری")
    password: str = Field(min_length=6, max_length=128, description="رمز عبور")
    full_name: str | None = Field(None, max_length=120, description="نام کامل (اختیاری)")


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    role: str
    created_at: datetime
    last_login_at: datetime | None = None


TokenOut.model_rebuild()
