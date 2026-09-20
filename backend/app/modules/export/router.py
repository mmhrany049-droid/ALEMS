"""Export — FastAPI router (doc 06: GET /export/pdf|excel|json).

JSON با envelope معمولی؛ Excel/PDF باینری با Content-Disposition (فایل دانلودی).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.export import service
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["export"])


@router.get("/export/json")
def export_json(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(service.full_json(db, student))


@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    data = service.excel_bytes(db, student)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="alems-export.xlsx"'},
    )


@router.get("/export/pdf")
def export_pdf(
    report: str = Query(default="weekly", pattern="^(daily|weekly|monthly|summary)$"),
    when: str | None = Query(default=None, max_length=20),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    data = service.pdf_bytes(db, student, report, when)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="alems-report-{report}.pdf"'},
    )
