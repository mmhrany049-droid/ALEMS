"""سرویس تنظیمات — خواندن/نوشتن با مقادیر پیش‌فرض دامنه."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.modules.activity.domain import ReviewPolicy
from app.modules.exam.domain import ExamPolicy, ScoringPolicy
from app.modules.planning.domain import PlanningPolicy
from app.modules.settings.domain import DefaultPolicies
from app.modules.settings.models import AppSetting

DEFAULTS = DefaultPolicies()

KEY_SCORING = "scoring_policy"
KEY_REVIEW = "review_policy"
KEY_EXAM = "exam_policy"
KEY_PLANNING = "planning_policy"
KEY_GENERAL = "general"

_WRITABLE_KEYS = {KEY_SCORING, KEY_REVIEW, KEY_EXAM, KEY_PLANNING, KEY_GENERAL}


def get_setting(db: Session, key: str) -> dict | None:
    row = db.get(AppSetting, key)
    return row.value if row else None


def set_setting(db: Session, key: str, value: dict) -> dict:
    if key not in _WRITABLE_KEYS:
        raise ValueError(f"کلید تنظیمات نامعتبر است: {key}")
    row = db.get(AppSetting, key)
    if row is None:
        row = AppSetting(key=key, value=value)
        db.add(row)
    else:
        current = row.value or {}
        current.update(value)
        row.value = current
    db.commit()
    return row.value


def get_scoring_policy(db: Session) -> ScoringPolicy:
    data = get_setting(db, KEY_SCORING) or {}
    penalty = float(data.get("wrong_penalty", DEFAULTS.scoring.wrong_penalty))
    if not (0 <= penalty <= 1):
        penalty = DEFAULTS.scoring.wrong_penalty
    return ScoringPolicy(wrong_penalty=penalty)


def get_review_policy(db: Session) -> ReviewPolicy:
    return ReviewPolicy.from_settings(get_setting(db, KEY_REVIEW))


def get_exam_policy(db: Session) -> ExamPolicy:
    data = get_setting(db, KEY_EXAM) or {}
    max_q = int(data.get("max_questions", DEFAULTS.exam.max_questions))
    return ExamPolicy(max_questions=max_q)


def get_planning_policy(db: Session) -> PlanningPolicy:
    return PlanningPolicy.from_settings(get_setting(db, KEY_PLANNING))


def all_settings(db: Session) -> dict[str, Any]:
    """تنظیمات کامل + پیش‌فرض‌های دامنه."""
    result = DEFAULTS.as_dict()
    for key in _WRITABLE_KEYS:
        stored = get_setting(db, key)
        if stored:
            merged = dict(result.get(key, {}))
            merged.update(stored)
            result[key] = merged
    return result


def update_settings(db: Session, payload: dict[str, Any]) -> dict[str, Any]:
    """به‌روزرسانی تنظیمات — کلیدهای ناشناخته نادیده گرفته می‌شوند."""
    for key, value in payload.items():
        if key in _WRITABLE_KEYS and isinstance(value, dict):
            set_setting(db, key, value)
    return all_settings(db)
