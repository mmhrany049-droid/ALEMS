"""Report — FastAPI router (doc 06: GET /reports/daily|weekly|monthly)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.report import service
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["report"])


@router.get("/reports/daily")
def daily(
    date: str | None = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.daily(db, student, date))


@router.get("/reports/weekly")
def weekly(
    week_start: str | None = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.weekly(db, student, week_start))


@router.get("/reports/monthly")
def monthly(
    month: str | None = Query(default=None, max_length=10),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.monthly(db, student, month))
