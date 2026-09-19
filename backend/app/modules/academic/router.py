"""روتر ماژول دانش آموزشی — /api/v1/subjects، /resources"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.academic import service
from app.shared.exceptions import ValidationError
from app.shared.response import PageParams, ok

router = APIRouter(tags=["academic"])


@router.get("/subjects", response_model=dict)
def get_subjects(
    field: str | None = Query(None, description="فیلتر رشته"),
    grade: str | None = Query(None, description="فیلتر پایه"),
    db: Session = Depends(get_db),
) -> dict:
    """درخت دروس مطابق رشته و پایه (AT-06)."""
    subjects = service.list_subjects(db, field=field, grade=grade)
    return ok([service.subject_payload(s) for s in subjects])


@router.get("/subjects/{subject_id}/chapters", response_model=dict)
def get_chapters(subject_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    chapters = service.list_chapters(db, subject_id)
    return ok([service.chapter_payload(c) for c in chapters])


@router.get("/chapters/{chapter_id}/topics", response_model=dict)
def get_topics(chapter_id: uuid.UUID, db: Session = Depends(get_db)) -> dict:
    topics = service.list_topics(db, chapter_id)
    return ok([service.topic_payload(t) for t in topics])


class ImportBookIn(BaseModel):
    update_existing: bool = False


@router.post("/resources/import-book", response_model=dict)
async def import_book_endpoint(
    body: dict,
    update_existing: bool = Query(False, description="به‌روزرسانی کتاب تکراری"),
    db: Session = Depends(get_db),
) -> dict:
    """وارد کردن کتاب تست از فایل JSON (AT-07/AT-08).

    بدنه می‌تواند خودِ JSON کتاب باشد یا در کلید «book» قرار بگیرد.
    """
    data = body.get("book") if isinstance(body, dict) and isinstance(body.get("book"), dict) else body
    if not isinstance(data, dict):
        raise ValidationError("بدنه درخواست باید یک شیء JSON معتبر (کتاب تست) باشد.")
    result = service.import_book(db, data, update_existing=update_existing)
    return ok(result)


@router.get("/resources", response_model=dict)
def get_resources(
    subject_id: uuid.UUID | None = Query(None),
    type: str | None = Query(None, alias="type", description="نوع منبع"),
    db: Session = Depends(get_db),
) -> dict:
    resources = service.list_resources(db, subject_id=subject_id, type_=type)
    return ok([service.resource_payload(r) for r in resources])


@router.get("/resources/{resource_id}/questions", response_model=dict)
def get_resource_questions(
    resource_id: uuid.UUID,
    topic_id: uuid.UUID | None = Query(None),
    page: PageParams = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """سوالات یک منبع با مبحث و سختی (AT-09)."""
    questions, total = service.list_questions(
        db, resource_id, topic_id=topic_id, limit=page.page_size, offset=page.offset
    )
    return ok(
        [service.question_payload(q) for q in questions],
        meta=page.meta(total),
    )
