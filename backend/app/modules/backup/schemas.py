"""Backup & Restore — Pydantic v2 schemas (doc 06 §Backup)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BackupCreateIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    label: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=4, max_length=128)  # AES اختیاری (doc 03 §3.6)


class BackupRestoreIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1, max_length=64)
    confirm: bool = False  # V2-S02 — بدون confirm=true بازیابی رد می‌شود
    password: str | None = Field(default=None, max_length=128)
