"""مقادیر پیش‌فرض تنظیمات — هر سیاست در دامنه ماژول خودش تعریف شده است.

این فایل فقط نقشه کلیدهای تنظیمات و مقادیر پیش‌فرض را جمع می‌کند.
هیچ منطق کسب‌وکاری اینجا hard-code نمی‌شود؛ همه‌چیز از تنظیمات قابل بازنویسی است.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.activity.domain import ReviewPolicy
from app.modules.exam.domain import ExamPolicy, ScoringPolicy
from app.modules.planning.domain import PlanningPolicy


@dataclass
class DefaultPolicies:
    """مجموعه سیاست‌های پیش‌فرض ذخیره‌شده در تنظیمات."""

    scoring: ScoringPolicy = field(default_factory=ScoringPolicy)
    review: ReviewPolicy = field(default_factory=ReviewPolicy)
    exam: ExamPolicy = field(default_factory=ExamPolicy)
    planning: PlanningPolicy = field(default_factory=PlanningPolicy)

    def as_dict(self) -> dict:
        return {
            "scoring_policy": {"wrong_penalty": self.scoring.wrong_penalty},
            "review_policy": self.review.to_settings(),
            "exam_policy": {"max_questions": self.exam.max_questions},
            "planning_policy": {
                "default_free_start": self.planning.default_free_start,
                "default_free_end": self.planning.default_free_end,
                "session_minutes": self.planning.session_minutes,
                "break_minutes": self.planning.break_minutes,
                "max_daily_items": self.planning.max_daily_items,
            },
        }
