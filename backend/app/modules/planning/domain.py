"""Planning & Capacity & Today Hub — pure domain rules, NO I/O (doc 03 §3.1).

doc 11: ظرفیت (۱۱.۲)، pipeline ثابت تولید هفته (۱۱.۳)، manual override (۱۱.۴)،
recovery بدون dump روی فردا (۱۱.۵)، priority vs recommendation (۱۱.۶).
doc 08 §8.6-8.7 و §8.10 (reason code فارسی).

همه قواعد اینجا تابع خالص‌اند — unit-testable، بدون hard-code پراکنده (doc 10 §10.4).
"""
from __future__ import annotations

import math
from typing import Any

# --- pipeline ثابت (doc 11.3 — کد باید همین ترتیب را لاگ کند) -------------------------

PIPELINE: tuple[str, ...] = (
    "load_context",      # 1
    "exams",             # 2
    "goals",             # 3
    "taught_filter",     # 4
    "learning_states",   # 5
    "review_demand",     # 6
    "priority_items",    # 7
    "capacity_per_day",  # 8
    "allocate_tasks",    # 9
    "overload_check",    # 10
    "explain",           # 11
    "save_suggested",    # 12 — suggested نه locked
)

# --- ثابت‌های ظرفیت (doc 11.2، doc 08 §8.6) -------------------------------------------

# دقایق آزاد پیش‌فرض هر روز وقتی time block تعریف نشده (0=شنبه … 6=جمعه)
DEFAULT_FREE_MINUTES: dict[int, int] = {0: 240, 1: 240, 2: 240, 3: 240, 4: 240, 5: 420, 6: 540}

AVG_TASK_MINUTES = 45       # میانگین یک کار
SESSION_TARGET_MINUTES = 90 # وعده‌ها ۶۰–۱۲۰ دقیقه (doc 11.2) → هدف ۹۰
SESSION_MIN = 60
MAX_TASKS_DAY = 12
DEFAULT_COMPLETION_RATE = 0.7  # سابقه‌ای نیست → خوش‌بینانه ملایم
MIN_AVAILABLE_FOR_TASK = 20

# state (energy/focus) وزن پایین دارد (doc 11.2: اختیاری وزن پایین)
STATE_WEIGHT_ENERGY = 0.08
STATE_WEIGHT_FOCUS = 0.04
STATE_FACTOR_BOUNDS = (0.85, 1.15)

# --- priority / recommendation ----------------------------------------------------------

REASON_LABELS_FA: dict[str, str] = {
    "weakness": "نقطه ضعف یادگیری",
    "low_readiness": "آمادگی آزمون پایین",
    "review_due": "مرور سررسیده",
    "review_critical": "مرور بحرانی (غلط تکراری)",
    "goal": "هدف این هفته",
    "today_task": "کار امروز",
    "recovery": "جبران عقب‌افتادگی",
    "no_demand": "نیازی ثبت نشده — امروز سبک است",
    "exam_prep": "آمادگی آزمون نزدیک",
}


def reason_fa(code: str) -> str:
    return REASON_LABELS_FA.get(code, code)


# --- ظرفیت (doc 11.2) --------------------------------------------------------------------

def block_minutes(start_minutes: int, end_minutes: int) -> int:
    return max(0, end_minutes - start_minutes)


def day_availability(blocks: list[dict]) -> dict[str, Any]:
    """school/class زمان را اشغال می‌کنند؛ free ظرفیت مطالعه است (doc 08 §8.6)."""
    school = sum(block_minutes(b["start_minutes"], b["end_minutes"]) for b in blocks if b["kind"] == "school")
    klass = sum(block_minutes(b["start_minutes"], b["end_minutes"]) for b in blocks if b["kind"] == "class")
    free = sum(block_minutes(b["start_minutes"], b["end_minutes"]) for b in blocks if b["kind"] == "free")
    return {
        "school_minutes": school,
        "class_minutes": klass,
        "free_minutes": free,
        "has_blocks": bool(blocks),
    }


def completion_rate(done: int, total: int, default: float = DEFAULT_COMPLETION_RATE) -> float:
    """میانگین completion هفت روز اخیر — بدون سابقه → پیش‌فرض."""
    if total <= 0:
        return default
    return max(0.0, min(1.0, done / total))


def state_factor(energy: int | None, focus: int | None) -> float:
    """وزن پایین state روی ظرفیت (doc 11.2). مقیاس ۱..۵، مرکز ۳."""
    lo, hi = STATE_FACTOR_BOUNDS
    if energy is None and focus is None:
        return 1.0
    f = 1.0
    if energy is not None:
        f += STATE_WEIGHT_ENERGY * (energy - 3) / 2.0
    if focus is not None:
        f += STATE_WEIGHT_FOCUS * (focus - 3) / 2.0
    return max(lo, min(hi, f))


def compute_capacity(
    free_minutes: int,
    weekday: int,
    has_blocks: bool,
    done_7d: int,
    total_7d: int,
    energy: int | None = None,
    focus: int | None = None,
) -> dict[str, Any]:
    """خروجی doc 11.2: available_minutes + suggested_task_count + suggested_session_count."""
    base = free_minutes if has_blocks else DEFAULT_FREE_MINUTES.get(weekday, 240)
    rate = completion_rate(done_7d, total_7d)
    factor = state_factor(energy, focus)
    available = int(round(base * rate * factor))
    available = max(0, available)

    if available < MIN_AVAILABLE_FOR_TASK:
        tasks = 0
    else:
        tasks = max(1, min(MAX_TASKS_DAY, round(available / AVG_TASK_MINUTES)))

    if available < SESSION_MIN:
        sessions = 0
    else:
        sessions = max(1, min(round(available / SESSION_TARGET_MINUTES), available // SESSION_MIN))

    return {
        "available_minutes": available,
        "suggested_task_count": tasks,
        "suggested_session_count": sessions,
        "completion_rate": round(rate, 3),
        "state_factor": round(factor, 3),
        "base_free_minutes": base,
    }


# --- priority (doc 11.6: چه مباحثی این هفته مهم‌اند) -------------------------------------

def priority_score(exam_readiness: float, weakness: bool, review_due_count: int) -> float:
    """ترکیب learning state + تقاضای مرور — هرچه بالاتر، مهم‌تر."""
    readiness = max(0.0, min(1.0, exam_readiness))
    return round(
        0.5 * (1.0 - readiness) + (0.3 if weakness else 0.0) + 0.2 * min(1.0, review_due_count / 10.0),
        4,
    )


def priority_reason_codes(exam_readiness: float, weakness: bool, review_due_count: int) -> list[str]:
    codes: list[str] = []
    if review_due_count > 0:
        codes.append("review_due")
    if weakness:
        codes.append("weakness")
    if exam_readiness < 0.5:
        codes.append("low_readiness")
    return codes or ["low_readiness"]


# --- تخصیص هفته (doc 11.3 مراحل ۹-۱۰) ---------------------------------------------------

def allocate_week(
    week_days: list[dict],
    review_demand: dict[str, dict],
    priority_topics: list[dict],
    max_daily_review: int,
) -> list[dict]:
    """week_days: [{date, weekday, available_minutes, suggested_task_count, locked_count,
    locked_minutes}] → لیست taskهای پیشنهادی (source در service ست می‌شود).

    ۱) مرور هر روز از تقاضای همان روز (سقف max_daily_review)
    ۲) مطالعه/تست از priority topics پخش در روزهای با ظرفیت باقی‌مانده
    """
    alloc: list[dict] = []
    used: dict[str, dict] = {
        d["date"]: {"tasks": d.get("locked_count", 0), "minutes": d.get("locked_minutes", 0)}
        for d in week_days
    }
    caps = {d["date"]: d for d in week_days}

    # ۱) مرور
    for d in week_days:
        dem = review_demand.get(d["date"]) or {}
        n = int(dem.get("count", 0))
        if n <= 0:
            continue
        n = min(n, max_daily_review)
        room = caps[d["date"]]["suggested_task_count"] - used[d["date"]]["tasks"]
        minutes = min(90, n * 10)
        if room <= 0 or used[d["date"]]["minutes"] + minutes > caps[d["date"]]["available_minutes"]:
            continue
        alloc.append(
            {
                "date": d["date"],
                "kind": "review",
                "title": f"مرور {n} آیتم سررسیده",
                "topic_id": None,
                "topic_title": None,
                "book_title": None,
                "minutes": minutes,
                "count": n,
                "reason_code": "review_critical" if dem.get("critical") else "review_due",
            }
        )
        used[d["date"]]["tasks"] += 1
        used[d["date"]]["minutes"] += minutes

    # ۲) مطالعه/تست از priority — پخش round-robin در هفته، هر topic حداکثر ۲ کار
    per_topic = {t["topic_id"]: 0 for t in priority_topics}
    ndays = len(week_days)
    cursor = 0  # روز بعدی برای تخصیص — پخش یکنواخت به‌جای انباشت روی اولین روز
    placed = True
    round_i = 0
    while placed and round_i < 2:
        placed = False
        round_i += 1
        for t in priority_topics:
            tid = t["topic_id"]
            if per_topic[tid] >= 2:
                continue
            kind = "test" if round_i == 1 and "weakness" in (t.get("reason_codes") or []) else "study"
            minutes = 60 if kind == "test" else AVG_TASK_MINUTES
            for step_i in range(ndays):
                d = week_days[(cursor + step_i) % ndays]
                u = used[d["date"]]
                cap = caps[d["date"]]
                if u["tasks"] + 1 > cap["suggested_task_count"]:
                    continue
                if u["minutes"] + minutes > cap["available_minutes"]:
                    continue
                alloc.append(
                    {
                        "date": d["date"],
                        "kind": kind,
                        "title": ("تست " if kind == "test" else "مطالعه ") + (t.get("topic_title") or "مبحث"),
                        "topic_id": tid,
                        "topic_title": t.get("topic_title"),
                        "book_title": t.get("book_title"),
                        "minutes": minutes,
                        "count": 10 if kind == "test" else None,
                        "reason_code": (t.get("reason_codes") or ["low_readiness"])[0],
                    }
                )
                u["tasks"] += 1
                u["minutes"] += minutes
                per_topic[tid] += 1
                placed = True
                cursor = (cursor + step_i + 1) % ndays
                break
    return alloc


def overload_trim(day_tasks: list[dict], task_cap: int, available_minutes: int) -> tuple[list[dict], list[dict]]:
    """مرحله ۱۰ pipeline — اولویت حذف: study → test → review (مرور آخر از همه)."""
    order = {"study": 0, "test": 1, "review": 2}
    total_min = sum(t["minutes"] for t in day_tasks)
    keep = list(day_tasks)
    trimmed: list[dict] = []
    while (len(keep) > task_cap or total_min > available_minutes) and keep:
        victim = min(keep, key=lambda t: order.get(t["kind"], 0))
        keep.remove(victim)
        trimmed.append(victim)
        total_min -= victim["minutes"]
    return keep, trimmed


# --- recovery (doc 11.5 — ممنوع: انتقال ۱۰۰٪ به فردا) ------------------------------------

def spread_recovery(tasks: list[dict], remaining_days: list[str]) -> dict[str, list[dict]]:
    """tasks: [{id, critical}] · remaining_days: ISO dates asc (امروز به بعد).

    قانون: سقف هر روز = ceil(n / تعداد روزها)؛ critical اولویت روزهای زودتر را دارد
    ولی همه کارها روی اولین روز انباشته نمی‌شوند (V2-P04).
    """
    result: dict[str, list] = {d: [] for d in remaining_days}
    if not tasks or not remaining_days:
        return result
    n = len(tasks)
    cap = max(1, math.ceil(n / len(remaining_days)))
    counts = {d: 0 for d in remaining_days}
    ordered = sorted(tasks, key=lambda t: (not t.get("critical"), t.get("id", "")))
    for t in ordered:
        if t.get("critical"):
            day = min(remaining_days, key=lambda d: (counts[d], d))  # زودترین روز با کمترین بار
        else:
            day = next((d for d in remaining_days if counts[d] < cap), None)
            if day is None:  # همه پر — سبک‌ترین روز
                day = min(remaining_days, key=lambda d: (counts[d], d))
        result[day].append(t)
        counts[day] += 1
    return result


# --- recommendation (doc 11.6 — امروز چه کار مشخصی بکن) ----------------------------------

def recommendation_pick(
    today_tasks: list[dict],
    review_top: list[dict],
    top_priority: list[dict],
) -> dict[str, Any]:
    """payload + reasons (doc 08 §8.10: حداقل یک reason code قابل ترجمه فارسی)."""
    pending = [t for t in today_tasks if t.get("status") == "pending"]
    if pending:
        t = pending[0]
        reasons = ["today_task"]
        if t.get("reason_code") and t["reason_code"] not in reasons:
            reasons.append(t["reason_code"])
        return {
            "payload": {
                "kind": "task",
                "title": t.get("title"),
                "minutes": t.get("minutes"),
                "task_id": t.get("id"),
            },
            "reasons": reasons,
        }
    if review_top:
        critical = any(r.get("critical") for r in review_top)
        return {
            "payload": {
                "kind": "review",
                "title": f"مرور {len(review_top)} آیتم سررسیده",
                "review_item_id": review_top[0].get("id"),
            },
            "reasons": ["review_critical" if critical else "review_due"],
        }
    if top_priority:
        t = top_priority[0]
        return {
            "payload": {
                "kind": "study",
                "title": f"مطالعه {t.get('topic_title') or 'مبحث اولویت‌دار'}",
                "topic_id": t.get("topic_id"),
            },
            "reasons": t.get("reason_codes") or ["low_readiness"],
        }
    return {
        "payload": {"kind": "none", "title": "امروز سبک است — استراحت فعال یا مرور آزاد"},
        "reasons": ["no_demand"],
    }


# --- sparkline ---------------------------------------------------------------------------

def week_sparkline(days: list[dict]) -> list[dict]:
    """۷ روز اخیر برای Today Hub (doc 11.1) — ورودی آماده از service."""
    return days
