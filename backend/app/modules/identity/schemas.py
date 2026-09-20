"""User Identity — Pydantic v2 schemas (doc 06 §Auth)."""
from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.modules.student.schemas import StudentProfileOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128, description="حداقل ۸ کاراکتر")
    full_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str | None
    role: str
    created_at: dt.datetime


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserOut
    student: StudentProfileOut | None = None


class MeResponse(BaseModel):
    user: UserOut
    student: StudentProfileOut | None = None
