"""Review & Learning — Pydantic v2 schemas (doc 06 §Review)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PostponeIn(BaseModel):
    model_config = ConfigDict(extra="ignore")

    days: int = Field(default=1, ge=1, le=30)
