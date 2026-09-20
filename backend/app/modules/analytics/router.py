"""Analytics — FastAPI router (doc 06 §Analytics & Export)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.analytics import service
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["analytics"])


@router.get("/analytics/overview")
def overview(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.overview(db, student, days))


@router.get("/analytics/by-subject")
def by_subject(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.by_subject(db, student))


@router.get("/analytics/by-chapter")
def by_chapter(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.by_chapter(db, student))


@router.get("/analytics/by-topic")
def by_topic(
    order: str = Query(default="volume", pattern="^(volume|accuracy|readiness)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.by_topic(db, student, order, limit))


@router.get("/analytics/difficulty")
def by_difficulty(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.by_difficulty(db, student))


@router.get("/analytics/mistakes")
def mistakes(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.mistakes(db, student))
