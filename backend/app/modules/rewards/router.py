"""Motivation (Rewards & Behavior) — FastAPI router (doc 06 §Rewards)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.rewards import service
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["rewards"])


@router.get("/rewards/summary")
def summary(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.summary(db, student))


@router.get("/rewards/badges")
def badges(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.badges_out(db, student))
