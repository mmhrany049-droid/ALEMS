"""منطق دامنه برنامه‌ریزی — تولید برنامه هفتگی از زمان‌های آزاد و اهداف.

قوانین ۸.۴:
  - زمان‌های ثابت (مدرسه/کلاس) بلوک اشغال‌شده محسوب می‌شوند.
  - برنامه از زمان‌های آزاد (free) پر می‌شود؛ اگر آزاد تعریف نشده باشد از ساعات
    پیش‌فرض قابل تنظیم (policy) استفاده می‌شود.
خالص و قابل‌تست — بدون دیتابیس.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


@dataclass
class PlanningPolicy:
    """سیاست تولید برنامه — قابل بازنویسی از تنظیمات."""

    # ساعات پیش‌فرض مطالعه در روزهایی که زمان آزاد ثبت نشده است
    default_free_start: str = "16:00"
    default_free_end: str = "22:00"
    # طول هر جلسه مطالعه (دقیقه)
    session_minutes: int = 45
    # استراحت بین جلسات (دقیقه)
    break_minutes: int = 15
    # حداکثر آیتم برنامه هر روز
    max_daily_items: int = 8

    @classmethod
    def from_settings(cls, data: dict | None) -> "PlanningPolicy":
        policy = cls()
        if not data:
            return policy
        for key in ("default_free_start", "default_free_end", "session_minutes",
                    "break_minutes", "max_daily_items"):
            if key in data:
                setattr(policy, key, data[key])
        return policy


@dataclass
class OccupiedBlock:
    """بلوک اشغال‌شده (مدرسه/کلاس)."""

    start: dt.time
    end: dt.time
    title: str | None = None


def _parse_hhmm(value: str) -> dt.time:
    hour, minute = str(value).split(":")[:2]
    return dt.time(int(hour), int(minute))


def free_windows(
    occupied: list[OccupiedBlock],
    day_start: dt.time = dt.time(6, 0),
    day_end: dt.time = dt.time(23, 30),
) -> list[tuple[dt.time, dt.time]]:
    """محاسبه بازه‌های آزاد بین بلوک‌های اشغال‌شده در یک روز."""
    ranges = sorted(
        [(occ.start, occ.end) for occ in occupied if occ.start < occ.end],
        key=lambda r: r[0],
    )
    windows: list[tuple[dt.time, dt.time]] = []
    cursor = day_start
    for start, end in ranges:
        if start > cursor:
            windows.append((cursor, start))
        if end > cursor:
            cursor = end
    if cursor < day_end:
        windows.append((cursor, day_end))
    return [(s, e) for s, e in windows if _minutes(e) - _minutes(s) >= 15]


def _minutes(t: dt.time) -> int:
    return t.hour * 60 + t.minute


def generate_week_plan(
    *,
    week_start: dt.date,
    occupied_by_day: dict[int, list[OccupiedBlock]],
    goals: list[dict],
    policy: PlanningPolicy | None = None,
) -> dict[int, list[dict]]:
    """تولید برنامه هفتگی (شنبه تا جمعه) از زمان‌های آزاد و اهداف (AT-17).

    goals: [{"title", "subject", "minutes"}] — «minutes» سهم روزانه هر هدف است؛
    هر روز مستقل از سهم روزانه اهداف پر می‌شود (بلوک‌های مدرسه/کلاس اشغال هستند).
    خروجی: {day_of_week(0..6): [{"start", "end", "title", "type", "goal_id"?}]}
    """
    policy = policy or PlanningPolicy()
    session = int(policy.session_minutes)
    brk = int(policy.break_minutes)

    plan: dict[int, list[dict]] = {}
    for day in range(7):
        # صف کارهای این روز: سهم روزانه هر هدف
        queue: list[dict] = [
            {"title": g["title"], "subject": g.get("subject"),
             "remaining": int(g.get("minutes", session)), "goal_id": g.get("goal_id")}
            for g in goals if int(g.get("minutes", session)) > 0
        ]
        items: list[dict] = []
        occupied = occupied_by_day.get(day, [])
        windows = free_windows(occupied)
        for win_start, win_end in windows:
            cursor = _minutes(win_start)
            end_limit = _minutes(win_end)
            while queue and len(items) < policy.max_daily_items:
                task = queue[0]
                # آخرین تکه می‌تواند کوتاه‌تر از جلسه کامل باشد
                remaining_window = end_limit - cursor
                if remaining_window < 15:
                    break
                take = min(session, task["remaining"], remaining_window)
                if take < 15 and task["remaining"] > take:
                    break
                items.append({
                    "start": f"{cursor // 60:02d}:{cursor % 60:02d}",
                    "end": f"{(cursor + take) // 60:02d}:{(cursor + take) % 60:02d}",
                    "title": task["title"],
                    "subject": task["subject"],
                    "type": "study",
                    "goal_id": task["goal_id"],
                })
                task["remaining"] -= take
                if task["remaining"] <= 0:
                    queue.pop(0)
                cursor += take + brk
        plan[day] = items
    return plan


def summarize_week_items(items: list[dict]) -> dict:
    """خلاصه دقیقه‌ای برنامه."""
    total = 0
    by_subject: dict[str, int] = {}
    for item in items:
        minutes = _minutes(_parse_hhmm(item["end"])) - _minutes(_parse_hhmm(item["start"]))
        total += minutes
        subject = item.get("subject") or item.get("title") or "سایر"
        by_subject[subject] = by_subject.get(subject, 0) + minutes
    return {"total_minutes": total, "by_subject": by_subject}


def validate_time_range(start: str, end: str) -> tuple[dt.time, dt.time]:
    """اعتبارسنجی بازه زمانی — پایان باید بعد از شروع باشد."""
    try:
        start_t, end_t = _parse_hhmm(start), _parse_hhmm(end)
    except (ValueError, IndexError) as exc:
        raise ValueError("ساعت باید با قالب HH:MM باشد.") from exc
    if _minutes(end_t) <= _minutes(start_t):
        raise ValueError("ساعت پایان باید بعد از ساعت شروع باشد.")
    return start_t, end_t
