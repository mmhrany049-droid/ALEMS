"""Analytics — سازنده‌های خالص بلوک‌های متریک (doc 12 §12.1، doc 08 §8.5).

قانون طلایی پذیرش (V2-A01): Coverage / Accuracy / Volume همیشه سه بلوک
جدا هستند — هرگز در یک عدد قاطی نمی‌شوند.
"""
from __future__ import annotations

from typing import Any

ERROR_TYPE_FA = {
    "careless": "بی‌دقتی",
    "concept": "مفهومی",
    "method": "روش حل",
    "memory": "حافظه",
    "other": "سایر",
    None: "بدون برچسب",
}

TIME_BUCKETS_FA = ("شب", "صبح", "ظهر", "عصر")  # ترتیب ساعت: 0-5 شب، 5-12 صبح، 12-17 ظهر، 17-21 عصر


def time_bucket_fa(hour: int) -> str:
    """ساعت (۰–۲۳، تهران) → برچسب فارسی بازه زمانی."""
    if 5 <= hour < 12:
        return "صبح"
    if 12 <= hour < 17:
        return "ظهر"
    if 17 <= hour < 21:
        return "عصر"
    return "شب"


def ratio(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole > 0 else None


def answered_accuracy(correct: int, wrong: int) -> float | None:
    """دقت فقط روی پاسخ‌داده‌ها — «نزده» بی‌پاسخ نیست (قاعده ۳)."""
    return round(correct / (correct + wrong), 4) if (correct + wrong) > 0 else None


def coverage_block(
    topics_total: int,
    topics_attempted: int,
    questions_total: int,
    questions_attempted: int,
    by_resource: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """بلوک ۱ — پوشش: چه‌قدر از کتاب را دیده‌ای (ورودی: distinct دیده‌شده‌ها)."""
    out = {
        "topics_total": topics_total,
        "topics_attempted": topics_attempted,
        "topics_ratio": ratio(topics_attempted, topics_total),
        "questions_total": questions_total,
        "questions_attempted": questions_attempted,
        "questions_ratio": ratio(questions_attempted, questions_total),
    }
    if by_resource is not None:
        out["by_resource"] = by_resource
    return out


def accuracy_block(
    correct: int,
    wrong: int,
    unanswered: int,
    not_entered: int,
    percent_konkur: float | None,
    percent_no_penalty: float | None,
    penalty_k: float,
) -> dict[str, Any]:
    """بلوک ۲ — دقت: از آنچه زده‌ای چقدر درست بوده (جدا از پوشش و حجم)."""
    return {
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "not_entered": not_entered,
        "answered_accuracy": answered_accuracy(correct, wrong),
        "percent_konkur": percent_konkur,          # (C - k*W)/T — doc 08 §8.1
        "percent_no_penalty": percent_no_penalty,  # C/T — همیشه جدا
        "penalty_k": penalty_k,
    }


def volume_block(
    attempts: int,
    sessions: int,
    study_minutes: int,
    active_days: int,
    reviews_done: int,
    duration_seconds: int,
) -> dict[str, Any]:
    """بلوک ۳ — حجم: چقدر کار کرده‌ای (بدون قضاوت درست/غلط)."""
    return {
        "attempts": attempts,
        "sessions": sessions,
        "study_minutes": study_minutes,
        "test_duration_minutes": duration_seconds // 60,
        "active_days": active_days,
        "reviews_done": reviews_done,
        "avg_attempts_per_active_day": round(attempts / active_days, 1) if active_days else None,
    }


def target_message_fa(target: str | None, acc: float | None, cov: float | None) -> dict[str, Any]:
    """Konkur target tracker — فقط نمایش کیفی، بدون ادعای رتبه علمی (doc 12 §12.4)."""
    if not target:
        return {
            "has_target": False,
            "target": None,
            "level_fa": None,
            "message_fa": "هدف کنکورت را در پروفایل ثبت کن تا فاصله‌ات را کیفی نشان دهیم.",
            "based_on": {"answered_accuracy": acc, "topics_ratio": cov},
        }
    if acc is None or cov is None:
        level = "تازه شروع کرده‌ای"
        msg = "داده‌ی کافی نیست — با چند جلسه تست، فاصله‌ات با هدف مشخص‌تر می‌شود."
    elif acc >= 0.75 and cov >= 0.7:
        level = "نزدیک به هدف"
        msg = "دقت و پوشش هر دو خوب است — با مرور و شبیه‌سازی حفظش کن."
    elif acc >= 0.6:
        level = "در مسیر"
        msg = "دقت قابل قبول است — حالا پوشش مباحث باقی‌مانده را بالا ببر."
    elif cov >= 0.6:
        level = "پوشش خوب، دقت کم"
        msg = "زیاد خوانده‌ای ولی دقت پایین است — اول خطاهای تکراری را ببند."
    else:
        level = "ابتدای مسیر"
        msg = "روی دقت مباحث خوانده‌شده کار کن، بعد پوشش را گسترش بده."
    return {
        "has_target": True,
        "target": target,
        "level_fa": level,
        "message_fa": f"هدف: {target} — {msg}",
        "based_on": {"answered_accuracy": acc, "topics_ratio": cov},
    }
