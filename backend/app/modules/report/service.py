"""سرویس گزارش — روزانه، هفتگی، ماهانه (Report Module).

هفته از شنبه شروع می‌شود؛ گزارش ماهانه بر اساس تقویم جلالی است.
"""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.jalali import (
    format_jalali_long,
    jalali_month_range,
    jalali_weekday,
    to_jalali,
    week_end,
    week_start,
)
from app.modules.activity.models import LearningActivity, ReviewItem, TestRecord
from app.modules.activity.service import get_marks_map
from app.modules.analytics.domain import aggregate_counts
from app.modules.analytics.service import by_difficulty, by_subject, mistake_types
from app.modules.exam.models import Exam
from app.modules.settings.service import get_scoring_policy
from app.modules.student.models import StudentState
from app.shared.exceptions import ValidationError

ACTIVITY_LABELS = {"study": "مطالعه", "test": "تست‌زنی", "review": "مرور",
                   "class": "کلاس", "school": "مدرسه"}


def _test_stats(db: Session, student_id: uuid.UUID, from_d: dt.date, to_d: dt.date) -> dict:
    policy = get_scoring_policy(db)
    rows = db.execute(
        select(TestRecord.result, func.count()).where(
            TestRecord.student_id == student_id,
            TestRecord.solved_at >= dt.datetime.combine(from_d, dt.datetime.min.time()),
            TestRecord.solved_at <= dt.datetime.combine(to_d, dt.datetime.max.time()),
        ).group_by(TestRecord.result)
    ).all()
    counts = {"correct": 0, "wrong": 0, "blank": 0}
    for result, cnt in rows:
        if result in counts:
            counts[result] = int(cnt)
    return {**counts, **aggregate_counts(counts["correct"], counts["wrong"], counts["blank"], policy)}


def _activity_minutes(db: Session, student_id: uuid.UUID, from_d: dt.date,
                      to_d: dt.date) -> dict:
    rows = db.execute(
        select(LearningActivity.type, func.sum(LearningActivity.duration_minutes)).where(
            LearningActivity.student_id == student_id,
            LearningActivity.started_at >= dt.datetime.combine(from_d, dt.datetime.min.time()),
            LearningActivity.started_at <= dt.datetime.combine(to_d, dt.datetime.max.time()),
        ).group_by(LearningActivity.type)
    ).all()
    minutes = {t: int(m or 0) for t, m in rows}
    return {ACTIVITY_LABELS.get(t, t): v for t, v in minutes.items()}


def _state(db: Session, student_id: uuid.UUID, day: dt.date) -> dict | None:
    state = db.scalar(select(StudentState).where(
        StudentState.student_id == student_id, StudentState.date == day
    ))
    if state is None:
        return None
    return {"energy_level": state.energy_level, "mood": state.mood,
            "study_condition": state.study_condition, "note": state.note}


def _review_stats(db: Session, student_id: uuid.UUID, from_d: dt.date, to_d: dt.date) -> dict:
    done = db.scalar(select(func.count()).select_from(ReviewItem).where(
        ReviewItem.student_id == student_id,
        ReviewItem.status == "done",
        ReviewItem.reviewed_at >= dt.datetime.combine(from_d, dt.datetime.min.time()),
        ReviewItem.reviewed_at <= dt.datetime.combine(to_d, dt.datetime.max.time()),
    )) or 0
    pending = db.scalar(select(func.count()).select_from(ReviewItem).where(
        ReviewItem.student_id == student_id, ReviewItem.status == "pending"
    )) or 0
    return {"reviewed": int(done), "pending": int(pending)}


def daily_report(db: Session, student_id: uuid.UUID, day: dt.date) -> dict:
    """گزارش روزانه."""
    return {
        "type": "daily",
        "date": day.isoformat(),
        "date_label": format_jalali_long(day),
        "weekday": jalali_weekday(day),
        "weekday_label": ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"][jalali_weekday(day)],
        "activities_minutes": _activity_minutes(db, student_id, day, day),
        "tests": _test_stats(db, student_id, day, day),
        "review": _review_stats(db, student_id, day, day),
        "state": _state(db, student_id, day),
    }


def weekly_report(db: Session, student_id: uuid.UUID, week_start_date: dt.date) -> dict:
    """گزارش هفتگی — شنبه تا جمعه؛ هفته ناقص بر اساس روزهای موجود (قانون ۸.۶)."""
    start = week_start(week_start_date)
    end = week_end(week_start_date)
    today = dt.date.today()
    effective_end = min(end, today)

    per_day = []
    for i in range(7):
        day = start + dt.timedelta(days=i)
        if day > effective_end:
            break
        per_day.append({
            "date": day.isoformat(),
            "date_label": format_jalali_long(day),
            "tests": _test_stats(db, student_id, day, day),
            "activities_minutes": _activity_minutes(db, student_id, day, day),
        })

    return {
        "type": "weekly",
        "week_start": start.isoformat(),
        "week_end": end.isoformat(),
        "week_start_label": format_jalali_long(start),
        "week_end_label": format_jalali_long(end),
        "per_day": per_day,
        "activities_minutes": _activity_minutes(db, student_id, start, effective_end),
        "tests": _test_stats(db, student_id, start, effective_end),
        "review": _review_stats(db, student_id, start, effective_end),
        "by_subject": by_subject(db, student_id, start, effective_end),
        "mistakes": mistake_types(db, student_id, start, effective_end),
    }


def monthly_report(db: Session, student_id: uuid.UUID, jy: int, jm: int) -> dict:
    """گزارش ماهانه بر اساس تقویم جلالی."""
    if not (1 <= jm <= 12):
        raise ValidationError("شماره ماه جلالی باید بین ۱ تا ۱۲ باشد.")
    rng = jalali_month_range(jy, jm)
    today = dt.date.today()
    effective_end = min(rng.end, today)

    weekly_breaks = []
    cursor = week_start(rng.start)
    while cursor <= rng.end:
        weekly_breaks.append(cursor)
        cursor += dt.timedelta(days=7)

    weeks = []
    for week_s in weekly_breaks:
        week_e = min(week_end(week_s), rng.end)
        weeks.append({
            "week_start": week_s.isoformat(),
            "week_start_label": format_jalali_long(week_s),
            "tests": _test_stats(db, student_id, week_s, week_e),
            "activities_minutes": _activity_minutes(db, student_id, week_s, week_e),
        })

    return {
        "type": "monthly",
        "jalali_year": jy,
        "jalali_month": jm,
        "month_label": f"{to_jalali(rng.start)[1]:02d}",
        "range_start": rng.start.isoformat(),
        "range_end": rng.end.isoformat(),
        "activities_minutes": _activity_minutes(db, student_id, rng.start, effective_end),
        "tests": _test_stats(db, student_id, rng.start, effective_end),
        "review": _review_stats(db, student_id, rng.start, effective_end),
        "difficulty": by_difficulty(db, student_id, rng.start, effective_end),
        "by_subject": by_subject(db, student_id, rng.start, effective_end),
        "weeks": weeks,
    }


def exams_in_range(db: Session, student_id: uuid.UUID, from_d: dt.date,
                   to_d: dt.date) -> list[dict]:
    """آزمون‌های بازه — برای گزارش و Today Hub."""
    rows = db.scalars(
        select(Exam).where(
            Exam.student_id == student_id,
            Exam.scheduled_at >= dt.datetime.combine(from_d, dt.datetime.min.time()),
            Exam.scheduled_at <= dt.datetime.combine(to_d, dt.datetime.max.time()),
        ).order_by(Exam.scheduled_at)
    )
    return [
        {"id": str(e.id), "title": e.title, "exam_type": e.exam_type, "status": e.status,
         "scheduled_at": e.scheduled_at.isoformat(),
         "duration_minutes": e.duration_minutes,
         "percent_konkur": round(e.result.percent_konkur, 2)
         if e.result and e.result.percent_konkur is not None else None}
        for e in rows
    ]
