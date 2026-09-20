"""Student — application services (doc 06 §Student).

- profile GET/PUT (پایه/رشته/هدف)
- check-in: upsert per Tehran day (no duplicates — phase-1 acceptance)
- state: today/last/data_days
- taught topics: upsert with (student_id, topic_id) uniqueness;
  cascade rule in domain (real topic tree arrives with phase 2)
"""
from __future__ import annotations

import datetime as dt

from fastapi.exceptions import HTTPException
from sqlalchemy import func, select

from app.core.events import CHECKIN_SUBMITTED, Event, event_bus
from app.core.jalali import JalaliDate, gregorian_to_jalali, today_jalali
from app.modules.student import domain
from app.modules.student.models import CHECKIN_DIMENSIONS, Checkin, Student, TaughtTopic
from app.modules.student.schemas import (
    CheckinOut,
    StateOut,
    StudentProfileOut,
    TaughtTopicOut,
)


def _checkin_out(c: Checkin) -> CheckinOut:
    jy, jm, jd = gregorian_to_jalali(c.date.year, c.date.month, c.date.day)
    return CheckinOut(
        date=c.date,
        date_jalali=JalaliDate(jy, jm, jd).format(),
        energy=c.energy,
        focus=c.focus,
        motivation=c.motivation,
        stress=c.stress,
        fatigue=c.fatigue,
        updated_at=c.updated_at,
    )


def get_profile(student: Student) -> StudentProfileOut:
    return StudentProfileOut.model_validate(student)


def update_profile(db, student: Student, update) -> Student:
    data = update.model_dump(exclude_unset=True)
    for field in ("grade", "track", "target"):
        if field in data:
            setattr(student, field, data[field])
    student.updated_at = dt.datetime.now(dt.timezone.utc)
    db.flush()
    return student


def submit_checkin(db, student: Student, payload) -> Checkin:
    """Upsert: one check-in per (student, Tehran day) — never a duplicate."""
    errors = domain.validate_checkin_payload(payload.model_dump())
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])

    day = today_jalali().to_gregorian()
    checkin = db.execute(
        select(Checkin).where(Checkin.student_id == student.id, Checkin.date == day)
    ).scalar_one_or_none()

    created = checkin is None
    if checkin is None:
        checkin = Checkin(student_id=student.id, date=day)
        db.add(checkin)
    for d in CHECKIN_DIMENSIONS:
        setattr(checkin, d, getattr(payload, d))
    checkin.updated_at = dt.datetime.now(dt.timezone.utc)
    db.flush()

    event_bus.publish(Event(CHECKIN_SUBMITTED, {"student_id": student.id, "date": day.isoformat(), "created": created}))
    return checkin


def get_state(db, student: Student) -> StateOut:
    day = today_jalali().to_gregorian()
    today_row = db.execute(
        select(Checkin).where(Checkin.student_id == student.id, Checkin.date == day)
    ).scalar_one_or_none()
    last_row = db.execute(
        select(Checkin)
        .where(Checkin.student_id == student.id)
        .order_by(Checkin.date.desc())
        .limit(1)
    ).scalar_one_or_none()
    data_days = db.execute(
        select(func.count(func.distinct(Checkin.date))).where(Checkin.student_id == student.id)
    ).scalar_one()
    return StateOut(
        today=_checkin_out(today_row) if today_row else None,
        last=_checkin_out(last_row) if last_row else None,
        data_days=int(data_days),
    )


def get_taught(db, student: Student) -> list[TaughtTopicOut]:
    rows = db.execute(
        select(TaughtTopic).where(TaughtTopic.student_id == student.id).order_by(TaughtTopic.updated_at.desc())
    ).scalars().all()
    return [TaughtTopicOut.model_validate(r) for r in rows]


def set_taught(db, student: Student, body) -> list[TaughtTopicOut]:
    """Upsert each (topic_id, taught). Phase 1: no topic tree yet (empty cascade map)."""
    for it in body.items:
        row = db.execute(
            select(TaughtTopic).where(TaughtTopic.student_id == student.id, TaughtTopic.topic_id == it.topic_id)
        ).scalar_one_or_none()
        if row is None:
            row = TaughtTopic(student_id=student.id, topic_id=it.topic_id, taught=it.taught)
            db.add(row)
        else:
            row.taught = it.taught
        row.updated_at = dt.datetime.now(dt.timezone.utc)
    db.flush()
    return get_taught(db, student)
