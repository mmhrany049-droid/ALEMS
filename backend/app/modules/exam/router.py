"""Exam Center — FastAPI router (doc 06 §Exam: CRUD + start|submit + result)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.exam import service
from app.modules.exam.schemas import ExamIn, ExamSubmitIn, ExamUpdate
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["exam"])


@router.get("/exams")
def list_exams(
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.list_exams(db, student, status))


@router.post("/exams")
def create_exam(
    data: ExamIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    out = service.create_exam(db, student, data)
    db.commit()
    return ok(out)


@router.get("/exams/{exam_id}")
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.exam_out(db, service._get(db, student, exam_id)))


@router.put("/exams/{exam_id}")
def update_exam(
    exam_id: str,
    data: ExamUpdate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    out = service.update_exam(db, student, exam_id, data)
    db.commit()
    return ok(out)


@router.delete("/exams/{exam_id}")
def delete_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    out = service.delete_exam(db, student, exam_id)
    db.commit()
    return ok(out)


@router.post("/exams/{exam_id}/start")
def start_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    out = service.start_exam(db, student, exam_id)
    db.commit()
    return ok(out)


@router.post("/exams/{exam_id}/submit")
def submit_exam(
    exam_id: str,
    data: ExamSubmitIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    out = service.submit_exam(db, student, exam_id, data)
    db.commit()
    return ok(out)


@router.get("/exams/{exam_id}/result")
def exam_result(
    exam_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(service.exam_result(db, student, exam_id))
