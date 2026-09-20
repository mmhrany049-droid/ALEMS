"""Settings — Pydantic v2 schemas (doc 06: GET/PUT /settings)."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    review_intervals: list[int] | None = None
    include_blank_in_review: bool | None = None
    max_daily_review: int | None = None
    min_cluster: int | None = None
    konkurs_penalty_k: float | None = None
    streak_grace_days: int | None = None
