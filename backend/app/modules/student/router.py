"""روتر ماژول دانش‌آموز — /api/v1/students"""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.modules.student.schemas import ProfileIn, StateIn
from app.modules.student.service import (
    get_profile,
    list_states,
    profile_payload,
    state_payload,
    upsert_profile,
    upsert_state,
)
from app.shared.response import ok

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=dict)
def get_me_profile(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict:
    """پروفایل دانش‌آموز جاری."""
    return ok(profile_payload(get_profile(db, user.id)))


@router.put("/me", response_model=dict)
def update_me_profile(
    payload: ProfileIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ایجاد/به‌روزرسانی پروفایل (AT-04)."""
    profile = upsert_profile(db, user, payload)
    return ok(profile_payload(profile))


@router.post("/me/state", response_model=dict)
def post_state(
    payload: StateIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ثبت وضعیت روزانه — انرژی و حال (AT-05)."""
    state = upsert_state(db, user.id, payload)
    return ok(state_payload(state))


@router.get("/me/state", response_model=dict)
def get_states(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """لیست وضعیت روزانه در بازه (فیلترها inclusive)."""
    from app.modules.student.service import tehran_today

    today = tehran_today()
    states = list_states(db, user.id, from_date or today, to_date or today)
    return ok([state_payload(s) for s in states])
