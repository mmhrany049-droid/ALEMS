"""روتر ماژول آزمون — /api/v1/exams"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.exam.models import ExamQuestion
from app.modules.exam.schemas import ExamCreateIn, ExamSubmitIn
from app.modules.exam.service import (
    create_exam,
    exam_payload,
    get_exam,
    get_exam_result,
    list_exams,
    start_exam,
    submit_exam,
)
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.shared.response import PageParams, ok

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("", response_model=dict)
def post_exam(
    payload: ExamCreateIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ایجاد آزمون (AT-19)."""
    exam = create_exam(db, user.id, payload.model_dump())
    count = db.scalar(select(func.count()).select_from(ExamQuestion)
                      .where(ExamQuestion.exam_id == exam.id)) or 0
    return ok(exam_payload(exam, question_count=int(count)))


@router.get("", response_model=dict)
def get_exams(
    status: str | None = Query(None),
    page: PageParams = Depends(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    exams, total = list_exams(db, user.id, limit=page.page_size, offset=page.offset, status=status)
    return ok([exam_payload(e) for e in exams], meta=page.meta(total))


@router.get("/{exam_id}", response_model=dict)
def get_exam_detail(
    exam_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    exam = get_exam(db, user.id, exam_id)
    count = db.scalar(select(func.count()).select_from(ExamQuestion)
                      .where(ExamQuestion.exam_id == exam.id)) or 0
    return ok(exam_payload(exam, question_count=int(count)))


@router.get("/{exam_id}/questions", response_model=dict)
def get_exam_questions(
    exam_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """سوالات آزمون به ترتیب — برای اجرای آزمون."""
    from app.modules.academic.service import question_payload
    from app.modules.academic.models import Question as QModel

    exam = get_exam(db, user.id, exam_id)
    rows = db.execute(
        select(QModel, ExamQuestion.order_index)
        .join(ExamQuestion, ExamQuestion.question_id == QModel.id)
        .where(ExamQuestion.exam_id == exam.id)
        .order_by(ExamQuestion.order_index)
    ).all()
    return ok([question_payload(q) for q, _order in rows])


@router.post("/{exam_id}/start", response_model=dict)
def post_start(
    exam_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """شروع آزمون."""
    exam = start_exam(db, user.id, exam_id)
    return ok(exam_payload(exam))


@router.post("/{exam_id}/submit", response_model=dict)
def post_submit(
    exam_id: uuid.UUID,
    payload: ExamSubmitIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ثبت پاسخ‌ها و محاسبه نتیجه (AT-20/21/22)."""
    result = submit_exam(db, user.id, exam_id,
                         [a.model_dump() for a in payload.answers])
    return ok({
        "correct_count": result.correct_count,
        "wrong_count": result.wrong_count,
        "blank_count": result.blank_count,
        "percent_konkur": round(result.percent_konkur, 2) if result.percent_konkur is not None else None,
        "percent_no_penalty": round(result.percent_no_penalty, 2) if result.percent_no_penalty is not None else None,
        "difficulty_breakdown": result.difficulty_breakdown,
    })


@router.get("/{exam_id}/result", response_model=dict)
def get_result(
    exam_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(get_exam_result(db, user.id, exam_id))
