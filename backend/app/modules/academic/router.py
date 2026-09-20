"""Academic Knowledge (Books & Import) — FastAPI router (doc 06 §Books & Import).

مسیرها:
- POST /resources/import-book        (TOC-only مجاز — doc 08 §8.3)
- GET  /resources/import-book/schema (قبل از {id}/tree تعریف می‌شود)
- GET  /resources
- GET  /resources/{resource_id}/tree
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.academic import service
from app.modules.academic.schemas import BookImportRequest
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["academic"])


@router.post("/resources/import-book")
def import_book(
    body: BookImportRequest,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.import_book(db, student, body)
    db.commit()
    return ok(
        data=result,
        meta={"toc_only": True, "counts": result["resource"]["counts"]},
    )


@router.get("/resources/import-book/schema")
def import_book_schema(student: Student = Depends(get_current_student)):
    return ok(data=service.get_import_schema())


@router.get("/resources")
def list_resources(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data={"items": service.list_resources(db, student)})


@router.get("/resources/{resource_id}/tree")
def resource_tree(
    resource_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data=service.get_tree(db, student, resource_id))
