"""روتر ماژول فعالیت — /api/v1/activities، /test-records، /questions/{id}/marks"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.activity.schemas import ActivityIn, MarkIn, TestRecordsIn
from app.modules.activity.service import (
    activity_payload,
    add_mark,
    create_activity,
    create_test_records,
    list_activities,
    list_test_records,
    remove_mark,
    test_record_payload,
)
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.shared.exceptions import NotFoundError
from app.shared.response import PageParams, ok

router = APIRouter(tags=["activity"])


@router.post("/activities", response_model=dict)
def post_activity(
    payload: ActivityIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ثبت فعالیت مطالعه یا تست."""
    activity = create_activity(db, user.id, payload.model_dump())
    return ok(activity_payload(activity))


@router.get("/activities", response_model=dict)
def get_activities(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    type: str | None = Query(None),
    page: PageParams = Depends(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    import datetime as dt

    from_dt = dt.datetime.combine(from_date, dt.time.min) if from_date else None
    to_dt = dt.datetime.combine(to_date, dt.time.max) if to_date else None
    acts, total = list_activities(db, user.id, from_dt=from_dt, to_dt=to_dt,
                                  type_=type, limit=page.page_size, offset=page.offset)
    return ok([activity_payload(a) for a in acts], meta=page.meta(total))


@router.post("/test-records", response_model=dict)
def post_test_records(
    payload: TestRecordsIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ثبت نتیجه یک یا چند سوال (AT-10/AT-11/AT-12)."""
    records = create_test_records(db, user.id, [r.model_dump() for r in payload.records])
    return ok([test_record_payload(r) for r in records], meta={"count": len(records)})


@router.get("/test-records", response_model=dict)
def get_test_records(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    subject_id: uuid.UUID | None = Query(None),
    page: PageParams = Depends(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    records, total = list_test_records(db, user.id, from_date, to_date, subject_id,
                                       limit=page.page_size, offset=page.offset)
    return ok([test_record_payload(r) for r in records], meta=page.meta(total))


@router.post("/questions/{question_id}/marks", response_model=dict)
def post_mark(
    question_id: uuid.UUID,
    payload: MarkIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """افزودن تیک به سوال — یک سوال می‌تواند چند تیک همزمان داشته باشد."""
    mark = add_mark(db, user.id, question_id, payload.mark_type)
    return ok({"question_id": str(question_id), "mark_type": mark.mark_type,
               "created_at": mark.created_at.isoformat()})


@router.delete("/questions/{question_id}/marks/{mark_type}", response_model=dict)
def delete_mark(
    question_id: uuid.UUID,
    mark_type: str,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """حذف تیک سوال."""
    remove_mark(db, user.id, question_id, mark_type)
    return ok({"detail": "تیک حذف شد."})


@router.get("/questions/{question_id}/marks", response_model=dict)
def get_marks(
    question_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """تیک‌های فعلی یک سوال."""
    from app.modules.activity.models import QuestionMark
    from sqlalchemy import select

    rows = db.scalars(select(QuestionMark).where(
        QuestionMark.student_id == user.id, QuestionMark.question_id == question_id
    )).all()
    return ok([{"mark_type": m.mark_type, "created_at": m.created_at.isoformat()} for m in rows])
