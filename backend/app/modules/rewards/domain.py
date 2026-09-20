"""Motivation (Rewards & Behavior) — pure domain rules, NO I/O (doc 03 §3.1).

Points ledger append-only، streak شمسی، badge seed (OD4: ۸ تا ۱۲)، habit advice بعد از ۳۰ روز،
procrastination aid (doc 13).

قواعد این ماژول باید از توابع domain قابل‌تست بیایند؛ hard-code پراکنده ممنوع (doc 10 §10.4).
"""
from __future__ import annotations

import datetime as dt
import statistics
from collections.abc import Iterable
from typing import Any

from app.core.jalali import fa_digit

# --- 13.1 Points — رویدادهای امتیازآور (ledger append-only) --------------------------------
# رویدادها به event bus موجود map می‌شوند (doc 03 §3.4 — rewards مصرف‌کننده است):
#   PLAN_UPDATED(status=done) · REVIEW_COMPLETED · TEST_RECORDS_CREATED(finished) · CHECKIN_SUBMITTED
SOURCE_TASK = "plan_task.completed"
SOURCE_REVIEW = "review.completed"
SOURCE_SESSION = "test_session.finished"
SOURCE_CHECKIN = "checkin.submitted"

ALL_SOURCES = (SOURCE_TASK, SOURCE_REVIEW, SOURCE_SESSION, SOURCE_CHECKIN)

POINTS_BY_SOURCE: dict[str, int] = {
    SOURCE_TASK: 5,
    SOURCE_REVIEW: 2,
    SOURCE_SESSION: 10,
    SOURCE_CHECKIN: 3,
}

SOURCE_FA: dict[str, str] = {
    SOURCE_TASK: "تکمیل کار برنامه",
    SOURCE_REVIEW: "مرور کامل",
    SOURCE_SESSION: "اتمام جلسه تست",
    SOURCE_CHECKIN: "check-in روزانه",
}

CHECKIN_DAILY_CAP = 1  # doc 13.1 — سقف ۱ در روز

# --- 13.2 Streak ----------------------------------------------------------------------------
STREAK_GRACE_DEFAULT = 0      # «از دست دادن روز → reset؛ grace=0 پیش‌فرض»
STREAK_GRACE_MAX = 7


def streaks_from_days(active_days: Iterable[dt.date], today: dt.date, grace: int = STREAK_GRACE_DEFAULT) -> tuple[int, int]:
    """(current, longest) از مجموعه روزهای فعال (میلادی — معادل شمسی روز).

    - current: run پیوسته‌ای که به آخرین روز فعال ختم می‌شود، به‌شرطی که آن روز
      بیشتر از grace+1 روز از امروز عقب نباشد (روز جاری هنوز تمام نشده — streak
      دیروز تا پایان امروز زنده است). روز از دست رفته → reset (doc 13.2).
    - longest: بلندترین run پیوسته (بدون grace).
    """
    days = set(active_days)
    if not days:
        return (0, 0)
    longest = 0
    run = 0
    prev: dt.date | None = None
    for d in sorted(days):
        run = run + 1 if prev is not None and (d - prev).days == 1 else 1
        longest = max(longest, run)
        prev = d
    latest = max(days)
    if (today - latest).days > grace + 1:
        return (0, longest)
    current = 0
    d = latest
    while d in days:
        current += 1
        d -= dt.timedelta(days=1)
    return (current, longest)


# --- 13.3 Badges — seed (OD4: ۸ تا ۱۲ نشان) ----------------------------------------------------
# kind → کلید aggregate که service مقدارش را می‌سازد (از ledger و شمارش‌های مجاز)
BADGE_SEED: tuple[dict[str, Any], ...] = (
    {"code": "first_step", "title_fa": "قدم اول", "description_fa": "اولین فعالیت مطالعاتی معتبر", "kind": "active_days", "target": 1},
    {"code": "streak_3", "title_fa": "سه روز پیوسته", "description_fa": "۳ روز فعالیت پشت‌سرهم", "kind": "streak", "target": 3},
    {"code": "streak_7", "title_fa": "هفته طلایی", "description_fa": "۷ روز فعالیت پشت‌سرهم", "kind": "streak", "target": 7},
    {"code": "streak_30", "title_fa": "سی روز پولادین", "description_fa": "۳۰ روز فعالیت پشت‌سرهم", "kind": "streak", "target": 30},
    {"code": "reviewer_25", "title_fa": "مرورکننده", "description_fa": "۲۵ مرور کامل", "kind": "reviews", "target": 25},
    {"code": "tester_10", "title_fa": "ده جلسه تست", "description_fa": "۱۰ جلسه تست تمام‌شده", "kind": "sessions", "target": 10},
    {"code": "examiner", "title_fa": "آزمون‌داده", "description_fa": "اولین آزمون با نتیجه ثبت‌شده", "kind": "exams", "target": 1},
    {"code": "points_500", "title_fa": "۵۰۰ امتیاز", "description_fa": "مجموع امتیاز ۵۰۰", "kind": "points", "target": 500},
    {"code": "active_20", "title_fa": "بیست روز فعال", "description_fa": "۲۰ روز با فعالیت معتبر", "kind": "active_days", "target": 20},
    {"code": "answer_100", "title_fa": "صد پاسخ", "description_fa": "۱۰۰ پاسخ به سوال ثبت شد", "kind": "answers", "target": 100},
)

BADGE_KINDS = tuple({b["kind"] for b in BADGE_SEED})


def badge_earned(kind: str, value: int, target: int) -> bool:
    return value >= target


# --- 13.4 Habit advice — فقط اگر data_days >= 30 (doc 08 §8.9) --------------------------------
HABIT_MIN_DATA_DAYS = 30


def habit_advice(daily_done_counts: Iterable[int], data_days: int) -> dict[str, Any] | None:
    """data_days < 30 → None (هرگز نمایش داده نشود). وگرنه میانه انجام واقعی."""
    if data_days < HABIT_MIN_DATA_DAYS:
        return None
    counts = sorted(c for c in daily_done_counts if c > 0)
    if not counts:
        return None
    median = statistics.median(counts)
    suggested = max(1, int(median))
    return {
        "data_days": data_days,
        "median_done": median,
        "suggested_daily_tasks": suggested,
        "message_fa": (
            f"بر اساس میانهٔ انجام واقعی‌ات، روزی {fa_digit(str(suggested))} کار واقع‌بینانه است — "
            "نه بیشتر. عادت پایدار از تعداد کم و پیوسته ساخته می‌شود."
        ),
    }


# --- 13.5 Procrastination aid — ساده ----------------------------------------------------------------------------
PROCRAST_WINDOW_DAYS = 3
PROCRAST_RATE_THRESHOLD = 0.5
PROCRAST_BIG_TASK_MINUTES = 60


def procrastination_aid(
    day_stats: list[dict[str, Any]],
    big_tasks: list[dict[str, Any]],
    weak_topic: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """اگر چند روز completion_rate پایین و task بزرگ باز → split یا «۵ تست آسان از X».

    day_stats: [{done, total}] برای روزهای پنجره (فقط روزهایی که task دارند شمار می‌شوند).
    big_tasks: taskهای باز با minutes >= PROCRAST_BIG_TASK_MINUTES (service فیلتر می‌کند).
    """
    days_with_tasks = [d for d in day_stats if d["total"] > 0]
    if len(days_with_tasks) < 2:
        return None
    rates = [d["done"] / d["total"] for d in days_with_tasks]
    avg_rate = sum(rates) / len(rates)
    if avg_rate >= PROCRAST_RATE_THRESHOLD:
        return None
    if big_tasks:
        t = big_tasks[0]
        return {
            "kind": "split",
            "task_id": t["id"],
            "task_title": t["title"],
            "minutes": t["minutes"],
            "avg_completion_rate": round(avg_rate, 2),
            "message_fa": (
                f"«{t['title']}» {t['minutes']} دقیقه‌ای هنوز باز است — به دو بخش کوچک‌تر "
                "تقسیمش کن و فقط بخش اول را شروع کن."
            ),
        }
    if weak_topic is not None:
        title = weak_topic.get("topic_title") or "مبحث اولویت‌دار"
        return {
            "kind": "easy_start",
            "topic_id": weak_topic.get("topic_id"),
            "topic_title": weak_topic.get("topic_title"),
            "avg_completion_rate": round(avg_rate, 2),
            "message_fa": f"با ۵ تست آسان از «{title}» شروع کن — فقط برای اینکه به حرکت بیایی.",
        }
    return None
