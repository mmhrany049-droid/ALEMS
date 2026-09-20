"""Exam Center — فرمول‌های خالص (doc 08 §8.1، doc 12 §12.2).

scoring snapshot: درصد کنکوری و بدون‌جریمه همیشه جدا (هرگز یک عدد قاطی).
k از Settings (konkurs_penalty_k). T=0 → null. درصد منفی نمایش داده می‌شود.
"""
from __future__ import annotations

from typing import Any

KIND_LABELS_FA = {"mock": "آزمایشی", "school_subject": "امتحان درسی", "free": "آزاد"}
STATUS_LABELS_FA = {
    "planned": "برنامه‌ریزی‌شده",
    "in_progress": "در حال اجرا",
    "finished": "تمام‌شده",
    "cancelled": "لغوشده",
}

# انتقال‌های مجاز وضعیت
_ALLOWED = {
    "start": {"planned"},
    "submit": {"planned", "in_progress"},
    "cancel": {"planned", "in_progress"},
}


def can_transition(action: str, status: str) -> bool:
    return status in _ALLOWED.get(action, set())


def merge_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """جمع شمارش چند جلسه (mock چنددرس) + مجموع مدت واقعی."""
    out = {
        "total_count": sum(int(r.get("total_count") or 0) for r in rows),
        "correct_count": sum(int(r.get("correct_count") or 0) for r in rows),
        "wrong_count": sum(int(r.get("wrong_count") or 0) for r in rows),
        "unanswered_count": sum(int(r.get("unanswered_count") or 0) for r in rows),
        "not_entered_count": sum(int(r.get("not_entered_count") or 0) for r in rows),
        "actual_duration_seconds": sum(int(r.get("actual_duration_seconds") or 0) for r in rows),
    }
    return out


def scoring_snapshot(counts: dict[str, Any], k: float) -> dict[str, Any]:
    """doc 08 §8.1 — percent_konkur = (C - k*W)/T*100 · percent_no_penalty = C/T*100.

    T=0 → هر دو null. درصد منفی همان‌طور که هست (show_negative).
    """
    total = int(counts.get("total_count") or 0)
    correct = int(counts.get("correct_count") or 0)
    wrong = int(counts.get("wrong_count") or 0)
    percent_konkur: float | None = None
    percent_no_penalty: float | None = None
    if total > 0:
        percent_konkur = round((correct - k * wrong) / total * 100, 2)
        percent_no_penalty = round(correct / total * 100, 2)
    snap = dict(counts)
    snap.update(
        {
            "penalty_k": k,
            "percent_konkur": percent_konkur,
            "percent_no_penalty": percent_no_penalty,
        }
    )
    return snap


def duration_fa(seconds: int | None, planned_minutes: int | None) -> str | None:
    """مقایسه مدت واقعی با برنامه — «۲۵ دقیقه زودتر از برنامه» (نمایشی)."""
    if seconds is None or not planned_minutes:
        return None
    diff = planned_minutes * 60 - seconds
    mins = abs(diff) // 60
    if mins == 0:
        return "دقیقاً طبق برنامه"
    return f"{mins} دقیقه {'زودتر' if diff > 0 else 'دیرتر'} از برنامه"
