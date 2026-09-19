"""منطق دامنه تحلیل — تجمیع خالص شمارنده‌ها و درصدها (قابل‌تست)."""
from __future__ import annotations

from app.modules.exam.domain import ScoringPolicy, konkur_percent, no_penalty_percent


def aggregate_counts(correct: int, wrong: int, blank: int,
                     policy: ScoringPolicy | None = None) -> dict:
    """آمار استاندارد یک دسته: کل + درصدها (مطابق قوانین ۸.۱)."""
    total = correct + wrong + blank
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "blank": blank,
        "percent_konkur": round(konkur_percent(correct, wrong, total, policy), 2)
            if total > 0 else None,
        "percent_no_penalty": round(no_penalty_percent(correct, total), 2)
            if total > 0 else None,
    }
