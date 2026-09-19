"""سرویس دانش‌آموز — پروفایل و وضعیت روزانه."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.jalali import jalali_weekday
from app.modules.identity.models import User
from app.modules.student.models import GRADES, FIELDS, StudentProfile, StudentState
from app.modules.student.schemas import ProfileIn, StateIn, StateOut
from app.shared.exceptions import NotFoundError, ValidationError
from app.shared.response import ok


def get_profile(db: Session, user_id: uuid.UUID) -> StudentProfile | None:
    return db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))


def upsert_profile(db: Session, user: User, payload: ProfileIn) -> StudentProfile:
    profile = get_profile(db, user.id)
    if profile is None:
        profile = StudentProfile(user_id=user.id)
        db.add(profile)
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


def get_state(db: Session, user_id: uuid.UUID, day: date) -> StudentState | None:
    return db.scalar(
        select(StudentState).where(StudentState.student_id == user_id, StudentState.date == day)
    )


def upsert_state(db: Session, user_id: uuid.UUID, payload: StateIn) -> StudentState:
    day = payload.date or tehran_today()
    existing = get_state(db, user_id, day)
    if existing is not None:
        existing.energy_level = payload.energy_level
        existing.mood = payload.mood
        existing.study_condition = payload.study_condition
        existing.note = payload.note
        db.commit()
        db.refresh(existing)
        return existing
    state = StudentState(
        student_id=user_id,
        date=day,
        energy_level=payload.energy_level,
        mood=payload.mood,
        study_condition=payload.study_condition,
        note=payload.note,
    )
    db.add(state)
    db.commit()
    db.refresh(state)
    return state


def list_states(db: Session, user_id: uuid.UUID, from_date: date, to_date: date) -> list[StudentState]:
    if from_date > to_date:
        raise ValidationError("تاریخ شروع نمی‌تواند بعد از تاریخ پایان باشد.")
    return list(db.scalars(
        select(StudentState)
        .where(StudentState.student_id == user_id, StudentState.date >= from_date,
               StudentState.date <= to_date)
        .order_by(StudentState.date)
    ))


def tehran_today() -> date:
    """تاریخ امروز به وقت تهران."""
    import datetime as dt
    from zoneinfo import ZoneInfo

    return dt.datetime.now(ZoneInfo(settings.timezone)).date()


def profile_payload(profile: StudentProfile | None) -> dict:
    """خروجی استاندارد پروفایل + وضعیت کامل بودن + لیست مقادیر مجاز."""
    data = {
        "id": str(profile.id) if profile else None,
        "user_id": str(profile.user_id) if profile else None,
        "full_name": profile.full_name if profile else None,
        "grade": profile.grade if profile else None,
        "field": profile.field if profile else None,
        "academic_year": profile.academic_year if profile else None,
        "target_rank": profile.target_rank if profile else None,
        "target_major": profile.target_major if profile else None,
        "created_at": profile.created_at.isoformat() if profile else None,
        "is_complete": is_complete(profile),
    }
    return data


def is_complete(profile: StudentProfile | None) -> bool:
    return (
        profile is not None
        and bool(profile.full_name)
        and profile.grade in GRADES
        and profile.field in FIELDS
    )


def state_payload(state: StudentState) -> dict:
    out = StateOut.model_validate(state).model_dump(mode="json")
    out["weekday"] = jalali_weekday(state.date)  # ۰=شنبه ... ۶=جمعه
    return out


def require_profile(db: Session, user: User) -> StudentProfile:
    profile = get_profile(db, user.id)
    if profile is None:
        raise NotFoundError("پروفایل شما کامل نیست. ابتدا از بخش تنظیمات پروفایل را تکمیل کنید.")
    return profile
