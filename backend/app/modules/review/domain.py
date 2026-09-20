"""Review & Learning — pure domain rules, NO I/O (doc 03 §3.1, doc 10).

doc 10 §10.2 چرخه: intervals پیش‌فرض [1,3,7,14] روز؛ پس از اتمام چرخه → absorbed
(برنمی‌گردد مگر غلط جدید).
doc 08 §8.4: critical = wrong_count_on_question ≥ 2.
doc 10 §10.4: Learning State — فرمول‌های عددی فقط اینجا (توابع قابل‌تست)؛
hard-code پراکنده ممنوع.
doc 10 §10.5: ضعف = accuracy پایین + repeated_error بالا + coverage ناکافی
(نه فقط «آخرین تست غلط بود») — با گارد confidence.
"""
from __future__ import annotations

import datetime as dt

# --- صف مرور و چرخه -------------------------------------------------------------

SOURCES = ("wrong", "blank", "mark_review", "mark_important", "mark_hard")
SOURCE_LABELS_FA = {
    "wrong": "غلط",
    "blank": "نزده",
    "mark_review": "تیک مرور",
    "mark_important": "مهم",
    "mark_hard": "سخت",
}
STATUSES = ("pending", "scheduled", "absorbed")


def critical_flag(wrong_count: int) -> bool:
    """doc 08 §8.4 — critical اگر wrong_count_on_question ≥ 2."""
    return wrong_count >= 2


def next_after_complete(cycle_index: int, intervals: list[int], today: dt.date) -> dict:
    """complete → scheduled بعدی طبق چرخه (doc 10 §10.1-10.2).

    cycle_index = تعداد مرورهای انجام‌شده. مرور شماره i+1 → امروز + intervals[i].
    وقتی همه intervals مصرف شدند و همان مرور هم complete شد → absorbed.
    """
    if cycle_index < len(intervals):
        days = intervals[cycle_index]
        new_index = cycle_index + 1
        return {
            "status": "scheduled",
            "cycle_index": new_index,
            "scheduled_date": today + dt.timedelta(days=days),
            "next_interval_days": intervals[new_index] if new_index < len(intervals) else None,
        }
    return {"status": "absorbed", "cycle_index": cycle_index, "scheduled_date": None, "next_interval_days": None}


def postpone_date(current: dt.date | None, today: dt.date, days: int = 1) -> dt.date:
    """postpone → تاریخ جابه‌جا، status pending (doc 10 §10.1)."""
    return (current or today) + dt.timedelta(days=days)


def review_progress(cycle_index: int, intervals_len: int, absorbed: bool) -> float:
    """پیشرفت چرخه 0..1 — ورودی retention_est."""
    if absorbed:
        return 1.0
    if intervals_len <= 0:
        return 0.0
    return max(0.0, min(1.0, cycle_index / intervals_len))


def source_priority(source: str) -> int:
    """wrong قوی‌ترین منبع است (برای نمایش و اولویت)."""
    return {"wrong": 0, "mark_review": 1, "mark_hard": 2, "mark_important": 3, "blank": 4}.get(source, 5)


# --- Learning State (doc 10 §10.4) -------------------------------------------------

RECENCY_HALF_LIFE_DAYS = 7.0  # recency_score = 1/(1+days/7): امروز ۱، ۷ روز ۰٫۵

WEAKNESS_ACCURACY_BELOW = 0.5
WEAKNESS_REPEATED_AT_LEAST = 0.3
WEAKNESS_COVERAGE_BELOW = 0.6
WEAKNESS_CONFIDENCE_AT_LEAST = 0.3


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_coverage(attempted_questions: int, total_questions: int) -> float:
    """doc 08 §8.5 — نسبت واحدهای پوشش‌یافته (حداقل یک attempt غیر not_entered)."""
    if total_questions <= 0:
        return 0.0
    return _clamp01(attempted_questions / total_questions)


def compute_accuracy(correct: int, wrong: int) -> float:
    """doc 08 §8.5 — correct/(correct+wrong) روی attemptهای معتبر."""
    if correct + wrong <= 0:
        return 0.0
    return _clamp01(correct / (correct + wrong))


def compute_repeated_error(repeated_wrong_questions: int, attempted_questions: int) -> float:
    """سهم سوال‌هایی که ≥۲ بار غلط داشته‌اند (ورودی weakness و critical)."""
    if attempted_questions <= 0:
        return 0.0
    return _clamp01(repeated_wrong_questions / attempted_questions)


def compute_recency(days_since_last: float | None) -> float:
    """1 = امروز؛ با نیمه‌عمر ۷ روز کم می‌شود؛ بدون داده = 0."""
    if days_since_last is None:
        return 0.0
    return _clamp01(1.0 / (1.0 + max(0.0, days_since_last) / RECENCY_HALF_LIFE_DAYS))


def compute_retention(per_question: list[tuple[str, float]]) -> float:
    """میانگین ماندگاری هر سوال.

    per_question: [(latest_result, review_progress)] برای سوال‌های attemptشده.
    - correct: 0.6 + 0.4*progress (مرور کامل → 1.0)
    - wrong:   0.2*progress (بدون مرور → ~0)
    - blank/unknown: 0.3*progress (نزده یعنی رها، ولی رد نشده)
    """
    if not per_question:
        return 0.0
    vals = []
    for result, progress in per_question:
        if result == "correct":
            vals.append(0.6 + 0.4 * progress)
        elif result == "wrong":
            vals.append(0.2 * progress)
        else:
            vals.append(0.3 * progress)
    return _clamp01(sum(vals) / len(vals))


def compute_exam_readiness(coverage: float, accuracy: float, retention: float, repeated_error: float) -> float:
    """آمادگی آزمون — ترکیب وزن‌دار چهار بعد (همه 0..1)."""
    return _clamp01(0.40 * coverage + 0.35 * accuracy + 0.15 * retention + 0.10 * (1.0 - repeated_error))


def compute_confidence(valid_attempts: int, total_questions: int) -> float:
    """confidence بر اساس تعداد evidence — داده کم = اعتماد کم (جلوگیری از weakness زودرس)."""
    denom = max(6, total_questions)
    return _clamp01(valid_attempts / denom)


def is_weakness(coverage: float, accuracy: float, repeated_error: float, confidence: float, has_evidence: bool) -> bool:
    """doc 10 §10.5 — ضعف = ترکیب، نه فقط آخرین غلط."""
    if not has_evidence or confidence < WEAKNESS_CONFIDENCE_AT_LEAST:
        return False
    return (
        accuracy < WEAKNESS_ACCURACY_BELOW
        and repeated_error >= WEAKNESS_REPEATED_AT_LEAST
        and coverage < WEAKNESS_COVERAGE_BELOW
    )


def learning_state(
    total_questions: int,
    attempted_questions: int,
    correct_attempts: int,
    wrong_attempts: int,
    repeated_wrong_questions: int,
    valid_attempts: int,
    days_since_last: float | None,
    per_question_retention: list[tuple[str, float]],
) -> dict:
    """یک نقطه ورود برای همه فرمول‌ها — خروجی ستون‌های learning_states (doc 05)."""
    coverage = compute_coverage(attempted_questions, total_questions)
    accuracy = compute_accuracy(correct_attempts, wrong_attempts)
    repeated_error = compute_repeated_error(repeated_wrong_questions, attempted_questions)
    recency = compute_recency(days_since_last)
    retention = compute_retention(per_question_retention)
    readiness = compute_exam_readiness(coverage, accuracy, retention, repeated_error)
    confidence = compute_confidence(valid_attempts, total_questions)
    weakness = is_weakness(coverage, accuracy, repeated_error, confidence, valid_attempts > 0)
    return {
        "coverage": round(coverage, 4),
        "accuracy": round(accuracy, 4),
        "retention_est": round(retention, 4),
        "recency_score": round(recency, 4),
        "repeated_error_score": round(repeated_error, 4),
        "exam_readiness": round(readiness, 4),
        "confidence": round(confidence, 4),
        "weakness": weakness,
    }


# --- خوشه‌ها (doc 10 §10.3) ----------------------------------------------------------

def priority_key(item: dict, today: dt.date) -> tuple:
    """اولویت با critical و سررسید گذشته، بعد wrong_count بیشتر."""
    sched = item.get("scheduled_date") or today
    overdue = (today - sched).days if sched <= today else 0
    return (0 if item.get("critical") else 1, -overdue, -int(item.get("wrong_count") or 0))


def pick_cluster_suggestion(items: list[dict], today: dt.date, budget: int, min_cluster: int) -> list[dict]:
    """1) گروه‌بندی بر اساس topic 2) اولویت critical/سررسید گذشته
    3) پیشنهاد ≤ budget 4) خوشه ≥ min_cluster ترجیحاً با هم.
    """
    if budget <= 0 or not items:
        return []
    by_topic: dict[str, list[dict]] = {}
    for it in items:
        by_topic.setdefault(it.get("topic_id") or f"q:{it.get('id')}", []).append(it)
    for group in by_topic.values():
        group.sort(key=lambda it: priority_key(it, today))

    picked: list[dict] = []
    picked_ids: set[str] = set()

    # 1) خوشه‌های بزرگ (≥ min_cluster) با هم — به ترتیب criticalدارترین/بزرگ‌ترین
    big = sorted(
        (g for g in by_topic.values() if len(g) >= min_cluster),
        key=lambda g: (0 if any(x.get("critical") for x in g) else 1, -len(g)),
    )
    for group in big:
        if len(picked) + len(group) <= budget:
            for it in group:
                if it["id"] not in picked_ids:
                    picked.append(it)
                    picked_ids.add(it["id"])

    # 2) بقیه بودجه با اولویت فردی
    rest = sorted((it for it in items if it["id"] not in picked_ids), key=lambda it: priority_key(it, today))
    for it in rest:
        if len(picked) >= budget:
            break
        picked.append(it)
        picked_ids.add(it["id"])
    return picked
