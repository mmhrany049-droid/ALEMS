"""روتر ماژول مرور — /api/v1/reviews"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from pydantic import BaseModel, Field

from app.modules.activity.service import (
    complete_review,
    list_review_queue,
    postpone_review,
    reopen_review,
    review_item_payload,
)
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.shared.response import ok

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/queue", response_model=dict)
def get_queue(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    status: str = Query("pending", description="pending/done/all"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """لیست صف مرور امروز و آینده — اولویت بالا به پایین (AT-13)."""
    marks_map: dict[str, list[str]] = {}
    items = []
    if status == "all":
        pending = list_review_queue(db, user.id, from_date, to_date, "pending")
        done = list_review_queue(db, user.id, from_date, to_date, "done")
        rows = pending + done
    else:
        rows = list_review_queue(db, user.id, from_date, to_date, status)
    from app.modules.activity.service import get_marks_map as gmm

    marks_map = gmm(db, user.id)
    return ok([review_item_payload(item, marks_map.get(str(item.question_id), [])) for item in rows])


@router.post("/{item_id}/complete", response_model=dict)
def post_complete(
    item_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """علامت‌گذاری «مرور شد» + پیشنهاد مرور بعدی (چرخه ۱-۳-۷-۱۴) (AT-14)."""
    item = complete_review(db, user.id, item_id)
    return ok(review_item_payload(item))


class PostponeIn(BaseModel):
    days: int = Field(1, ge=1, le=30, description="چند روز بعد؟ (پیش‌فرض ۱)")


@router.post("/{item_id}/postpone", response_model=dict)
def post_postpone(
    item_id: uuid.UUID,
    payload: PostponeIn | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """«بعداً» — به‌عقب‌انداختن مرور (سند 07 §7.4)."""
    item = postpone_review(db, user.id, item_id,
                           days=payload.days if payload else 1)
    return ok(review_item_payload(item))


@router.post("/{item_id}/reopen", response_model=dict)
def post_reopen(
    item_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """بازگرداندن سوال به صف مرور."""
    item = reopen_review(db, user.id, item_id)
    return ok(review_item_payload(item))


@router.post("/rebuild", response_model=dict)
def post_rebuild(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """بازسازی صف مرور بر اساس قوانین (غلط‌ها + تیک‌ها + نزده‌های اختیاری)."""
    return ok(rebuild_result(db, user.id))


def rebuild_result(db: Session, student_id) -> dict:
    from app.modules.activity.service import rebuild_review_queue

    return rebuild_review_queue(db, student_id)
