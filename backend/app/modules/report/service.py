"""Report — گزارش روزانه/هفتگی/ماهانه (doc 12 §12.5).

سه بلوک متریک در هر گزارش جدا می‌مانند (V2-A01). هفته شنبه–جمعه؛
ماه شمسی («1405-06») یا میلادی («2026-09») قبول است.
"""
from __future__ import annotations

import calendar
import datetime as dt
import logging
import re
from typing import Any

from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.jalali import (
    gregorian_to_jalali,
    is_jalali_leap_year,
    jalali_month_days,
    jalali_to_gregorian,
)
from app.modules.analytics import domain
from app.modules.analytics.service import (
    TZ_TEHRAN,
    coverage_cumulative,
    range_facts,
)
from app.modules.exam.models import Exam
from app.modules.planning.models import CapacitySnapshot
from app.modules.planning.service import parse_date, week_of
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Checkin, Student

logger = logging.getLogger("alems.report")

MSG_BAD_MONTH = "ماه را مثل ۱۴۰۵-۰۶ یا 2026-09 وارد کن."


def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).astimezone(TZ_TEHRAN).date()


def _jalali_str(d: dt.date) -> str:
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


WEEKDAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


def _weekday_fa(d: dt.date) -> str:
    return WEEKDAYS_FA[(d.weekday() + 1) % 7]


def _accuracy_from_facts(f: dict[str, Any], k: float) -> dict[str, Any]:
    total = f.get("total_questions") or 0  # §8.1 — T = کل سوالات جلسات بازه
    pk = round((f["correct"] - k * f["wrong"]) / total * 100, 2) if total else None
    pnp = round(f["correct"] / total * 100, 2) if total else None
    return domain.accuracy_block(
        f["correct"], f["wrong"], f["unanswered"], f["not_entered"], pk, pnp, k
    )


def _volume_from_facts(f: dict[str, Any]) -> dict[str, Any]:
    return domain.volume_block(
        attempts=f["attempts"],
        sessions=f["sessions"],
        study_minutes=f["study_minutes"],
        active_days=f["active_days"],
        reviews_done=f["reviews_done"],
        duration_seconds=f["test_duration_minutes"] * 60,
    )


def _exams_in(db: Session, student: Student, start: dt.date, end: dt.date) -> list[dict[str, Any]]:
    rows = db.execute(
        select(Exam).where(
            Exam.student_id == student.id,
            Exam.scheduled_date.is_not(None),
            Exam.scheduled_date >= start,
            Exam.scheduled_date <= end,
        ).order_by(Exam.scheduled_date)
    ).scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "kind": e.kind,
            "status": e.status,
            "scheduled_date": e.scheduled_date.isoformat(),
            "scheduled_date_jalali": _jalali_str(e.scheduled_date),
            "percent_konkur": (e.scoring or {}).get("percent_konkur"),
            "percent_no_penalty": (e.scoring or {}).get("percent_no_penalty"),
        }
        for e in rows
    ]


def _capacity_usage(db: Session, student: Student, days: list[dt.date]) -> dict[str, Any]:
    rows = db.execute(
        select(CapacitySnapshot).where(
            CapacitySnapshot.student_id == student.id, CapacitySnapshot.date.in_(days)
        )
    ).scalars().all()
    available = sum(r.available_study_minutes or 0 for r in rows)
    return {
        "days_with_snapshot": len(rows),
        "available_minutes": available,
    }


# --- daily --------------------------------------------------------------------------------

def daily(db: Session, student: Student, date_raw: str | None = None) -> dict[str, Any]:
    d = parse_date(date_raw) if date_raw else _today()
    facts = range_facts(db, student, d, d)
    settings = get_settings_map(db)
    k = float(settings.get("konkurs_penalty_k", 0.33))

    checkin = db.execute(
        select(Checkin).where(Checkin.student_id == student.id, Checkin.date == d)
    ).scalar_one_or_none()

    cap_row = db.execute(
        select(CapacitySnapshot).where(CapacitySnapshot.student_id == student.id, CapacitySnapshot.date == d)
    ).scalar_one_or_none()

    return {
        "kind": "daily",
        "date": d.isoformat(),
        "date_jalali": _jalali_str(d),
        "weekday_fa": _weekday_fa(d),
        "coverage": coverage_cumulative(db, student),   # بلوک ۱ — جدا
        "accuracy": _accuracy_from_facts(facts, k),     # بلوک ۲ — جدا
        "volume": _volume_from_facts(facts),            # بلوک ۳ — جدا
        "plan": {
            "tasks_total": facts["tasks_total"],
            "tasks_done": facts["tasks_done"],
            "study_minutes": facts["study_minutes"],
        },
        "capacity": {
            "available_minutes": cap_row.available_study_minutes if cap_row else None,
            "used_minutes": facts["study_minutes"],
        },
        "reviews_done": facts["reviews_done"],
        "checkin": (
            {"energy": checkin.energy, "focus": checkin.focus, "motivation": checkin.motivation,
             "stress": checkin.stress, "fatigue": checkin.fatigue}
            if checkin else None
        ),
        "sessions": facts["session_items"],
        "exams": _exams_in(db, student, d, d),
        "top_topics": facts["top_topics"],
    }


# --- weekly --------------------------------------------------------------------------------

def weekly(db: Session, student: Student, week_start_raw: str | None = None) -> dict[str, Any]:
    anchor = parse_date(week_start_raw) if week_start_raw else _today()
    ws, days = week_of(anchor)
    we = days[-1]
    facts = range_facts(db, student, ws, we)
    settings = get_settings_map(db)
    k = float(settings.get("konkurs_penalty_k", 0.33))

    per_day = []
    for d in days:
        f = range_facts(db, student, d, d)
        per_day.append(
            {
                "date": d.isoformat(),
                "date_jalali": _jalali_str(d),
                "weekday_fa": _weekday_fa(d),
                "is_today": d == _today(),
                "attempts": f["attempts"],
                "correct": f["correct"],
                "wrong": f["wrong"],
                "study_minutes": f["study_minutes"],
                "tasks_done": f["tasks_done"],
                "tasks_total": f["tasks_total"],
                "reviews_done": f["reviews_done"],
                "answered_accuracy": f["answered_accuracy"],
            }
        )

    pws = ws - dt.timedelta(days=7)
    prev = range_facts(db, student, pws, pws + dt.timedelta(days=6))
    cap = _capacity_usage(db, student, days)
    used = facts["study_minutes"]
    usage_ratio = round(used / cap["available_minutes"], 3) if cap["available_minutes"] else None

    return {
        "kind": "weekly",
        "week_start": ws.isoformat(),
        "week_start_jalali": _jalali_str(ws),
        "week_end": we.isoformat(),
        "week_end_jalali": _jalali_str(we),
        "coverage": coverage_cumulative(db, student),   # بلوک ۱ — جدا
        "accuracy": _accuracy_from_facts(facts, k),     # بلوک ۲ — جدا
        "volume": _volume_from_facts(facts),            # بلوک ۳ — جدا
        "days": per_day,
        "capacity": {**cap, "used_minutes": used, "usage_ratio": usage_ratio},
        "previous_week": {
            "week_start": pws.isoformat(),
            "attempts": prev["attempts"],
            "study_minutes": prev["study_minutes"],
            "attempts_delta": facts["attempts"] - prev["attempts"],
            "study_minutes_delta": facts["study_minutes"] - prev["study_minutes"],
        },
        "exams": _exams_in(db, student, ws, we),
        "top_topics": facts["top_topics"],
        "sessions": facts["session_items"],
    }


# --- monthly -------------------------------------------------------------------------------

def _month_range(month_raw: str | None) -> tuple[dt.date, dt.date, str]:
    """«1405-06» (شمسی) یا «2026-09» (میلادی) یا None → ماه جاری شمسی."""
    if not month_raw:
        t = _today()
        jy, jm, _jd = gregorian_to_jalali(t.year, t.month, t.day)
        month_raw = f"{jy:04d}-{jm:02d}"
    m = re.fullmatch(r"(\d{4})[-/](\d{1,2})", month_raw.strip())
    if not m:
        raise HTTPException(status_code=422, detail=MSG_BAD_MONTH)
    y, mo = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        raise HTTPException(status_code=422, detail=MSG_BAD_MONTH)
    if y < 1500:  # شمسی
        length = jalali_month_days(y, mo)
        gy, gm, gd = jalali_to_gregorian(y, mo, 1)
        label = f"{y:04d}/{mo:02d}"
    else:  # میلادی
        length = calendar.monthrange(y, mo)[1]
        gy, gm, gd = y, mo, 1
        label = f"{y:04d}-{mo:02d}"
    first = dt.date(gy, gm, gd)
    return first, first + dt.timedelta(days=length - 1), label


def monthly(db: Session, student: Student, month_raw: str | None = None) -> dict[str, Any]:
    start, end, label = _month_range(month_raw)
    facts = range_facts(db, student, start, end)
    settings = get_settings_map(db)
    k = float(settings.get("konkurs_penalty_k", 0.33))

    # ردیف‌های هفتگی (شنبه‌شروع، برش خورده به مرز ماه)
    weeks = []
    ws, _ = week_of(start)
    while ws <= end:
        w_days = [ws + dt.timedelta(days=i) for i in range(7)]
        clipped = [d for d in w_days if start <= d <= end]
        if clipped:
            f = range_facts(db, student, clipped[0], clipped[-1])
            weeks.append(
                {
                    "week_start": clipped[0].isoformat(),
                    "week_start_jalali": _jalali_str(clipped[0]),
                    "days": len(clipped),
                    "attempts": f["attempts"],
                    "correct": f["correct"],
                    "wrong": f["wrong"],
                    "study_minutes": f["study_minutes"],
                    "tasks_done": f["tasks_done"],
                    "tasks_total": f["tasks_total"],
                    "answered_accuracy": f["answered_accuracy"],
                }
            )
        ws += dt.timedelta(days=7)

    return {
        "kind": "monthly",
        "month": label,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "start_jalali": _jalali_str(start),
        "end_jalali": _jalali_str(end),
        "coverage": coverage_cumulative(db, student),   # بلوک ۱ — جدا
        "accuracy": _accuracy_from_facts(facts, k),     # بلوک ۲ — جدا
        "volume": _volume_from_facts(facts),            # بلوک ۳ — جدا
        "weeks": weeks,
        "exams": _exams_in(db, student, start, end),
        "top_topics": facts["top_topics"],
    }
