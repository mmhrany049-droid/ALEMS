"""روتر ماژول گزارش — /api/v1/reports"""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.jalali import week_start as iso_week_start
from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.modules.report.service import daily_report, exams_in_range, monthly_report, weekly_report
from app.modules.student.service import tehran_today
from app.shared.response import ok

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=dict)
def get_daily(
    date: dt.date | None = Query(None, description="تاریخ (پیش‌فرض امروز)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    day = date or tehran_today()
    return ok(daily_report(db, user.id, day))


@router.get("/weekly", response_model=dict)
def get_weekly(
    week_start: dt.date | None = Query(None, alias="week_start",
                                       description="تاریخ هر روز از هفته (شنبه محاسبه می‌شود)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """گزارش هفتگی — هفته شنبه تا جمعه (AT-24)."""
    start = iso_week_start(week_start or tehran_today())
    payload = weekly_report(db, user.id, start)
    payload["exams"] = exams_in_range(db, user.id, start, start + dt.timedelta(days=6))
    return ok(payload)


@router.get("/monthly", response_model=dict)
def get_monthly(
    year: int = Query(..., ge=1300, le=1500, description="سال جلالی"),
    month: int = Query(..., ge=1, le=12, description="ماه جلالی"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(monthly_report(db, user.id, year, month))
