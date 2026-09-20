"""Activity & Test Engine — FastAPI router (doc 06 §Tests).

مسیرها:
- POST /test-sessions                      create session (mode timed/untimed)
- GET  /test-sessions                      تاریخچه جلسات
- GET  /test-sessions/{id}                 جزئیات + attempts (append-only) + aggregate موضوع
- POST /test-sessions/{id}/records         add records (ثبت تست سریع)
- POST /test-sessions/{id}/finish          scoring — ایدمپوتنت (V2-T02)
- POST /tests/past-import                  نتایج قدیمی با not_entered (V2-T03)
- GET  /test-engine/preview?resource_id&from&to&parity   preview انتخاب بازه
- GET  /tests/error-notebook               دفترچه خطا (پایه)
- PUT  /tests/error-notebook/{note_id}     نوع اشتباه + یادداشت
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.core.events import TEST_RECORDS_CREATED, Event, event_bus
from app.db.session import get_db
from app.modules.activity import service
from app.modules.activity.domain import PARITIES
from app.modules.activity.schemas import (
    ErrorNoteUpdate,
    FinishIn,
    MarkUpdate,
    PastImportIn,
    RecordsIn,
    SessionCreate,
)
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["activity"])


@router.post("/test-sessions")
def create_session(
    body: SessionCreate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.create_session(db, student, body)
    db.commit()
    return ok(data=result)


@router.get("/test-sessions")
def list_sessions(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data={"items": service.list_sessions(db, student)})


@router.get("/test-sessions/{session_id}")
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data=service.get_session(db, student, session_id))


@router.post("/test-sessions/{session_id}/records")
def add_records(
    session_id: str,
    body: RecordsIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.add_records(db, student, session_id, body)
    db.commit()
    return ok(data=result)


@router.post("/test-sessions/{session_id}/finish")
def finish_session(
    session_id: str,
    body: FinishIn | None = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.finish_session(db, student, session_id, body or FinishIn())
    db.commit()
    if not result["idempotent"]:
        # بعد از commit publish می‌شود تا مصرف‌کننده (review rebuild) داده را ببیند
        s = result["session"]
        event_bus.publish(
            Event(
                TEST_RECORDS_CREATED,
                {
                    "student_id": student.id,
                    "session_id": session_id,
                    "finished": True,
                    "correct": s["correct_count"],
                    "wrong": s["wrong_count"],
                    "percent_konkur": s["percent_konkur"],
                },
            )
        )
    return ok(data=result)


@router.post("/tests/past-import")
def past_import(
    body: PastImportIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.past_import(db, student, body)
    db.commit()
    # بعد از commit — مصرف‌کننده (review rebuild) نتیجه را می‌بیند
    event_bus.publish(
        Event(
            TEST_RECORDS_CREATED,
            {
                "student_id": student.id,
                "session_id": result["session"]["id"],
                "count": result["imported"] + result["updated"],
                "past": True,
            },
        )
    )
    return ok(data=result)


@router.get("/test-engine/preview")
def preview(
    resource_id: str = Query(...),
    topic_ids: str | None = Query(default=None, description="comma-separated"),
    from_number: int | None = Query(default=None, ge=1, alias="from"),
    to_number: int | None = Query(default=None, ge=1, alias="to"),
    parity: str = Query(default="any"),
    count: int | None = Query(default=None, ge=1),
    difficulty: int | None = Query(default=None, ge=1, le=5),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    if parity not in PARITIES:
        raise HTTPException(status_code=422, detail="parity باید یکی از any/odd/even باشد.")
    ids = [t.strip() for t in (topic_ids or "").split(",") if t.strip()]
    return ok(
        data=service.preview(db, student, resource_id, ids, from_number, to_number, parity, count, difficulty)
    )


@router.get("/tests/error-notebook")
def error_notebook(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data={"items": service.list_error_notes(db, student)})


@router.put("/tests/error-notebook/{note_id}")
def update_error_note(
    note_id: str,
    body: ErrorNoteUpdate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    note = service.update_error_note(db, student, note_id, body)
    db.commit()
    return ok(data=note)


@router.get("/questions/{question_id}/marks")
def get_marks(
    question_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data=service.get_marks(db, student, question_id))


@router.put("/questions/{question_id}/marks")
def put_marks(
    question_id: str,
    body: MarkUpdate,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.put_marks(db, student, question_id, body)
    db.commit()
    return ok(data=result)
