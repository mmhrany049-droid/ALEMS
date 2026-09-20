"""Student — FastAPI router (doc 06 §Student: /students/me*)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.student import service
from app.modules.student.models import Student
from app.modules.student.schemas import (
    CheckinRequest,
    CheckinOut,
    StateOut,
    StudentProfileOut,
    StudentProfileUpdate,
    TaughtTopicOut,
    TaughtTopicsUpdate,
)
from app.shared.deps import get_current_student, get_current_user
from app.shared.envelope import ok

router = APIRouter(tags=["student"])


@router.get("/students/me")
def get_profile(student: Student = Depends(get_current_student)):
    return ok(data=service.get_profile(student).model_dump(mode="json"))


@router.put("/students/me")
def put_profile(
    update: StudentProfileUpdate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    service.update_profile(db, student, update)
    db.commit()
    return ok(data=service.get_profile(student).model_dump(mode="json"))


@router.post("/students/me/checkin")
def checkin(
    body: CheckinRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    checkin = service.submit_checkin(db, student, body)
    db.commit()
    return ok(data=service.get_state(db, student).model_dump(mode="json"))


@router.get("/students/me/state")
def state(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data=service.get_state(db, student).model_dump(mode="json"))


@router.get("/students/me/taught-topics")
def taught_get(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data={"items": [t.model_dump(mode="json") for t in service.get_taught(db, student)]})


@router.put("/students/me/taught-topics")
def taught_put(
    body: TaughtTopicsUpdate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.set_taught(db, student, body)
    db.commit()
    return ok(data={"items": [t.model_dump(mode="json") for t in result]})
