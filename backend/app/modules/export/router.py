"""روتر ماژول خروجی — /api/v1/export"""
from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.export.service import export_excel, export_json, export_pdf
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.modules.student.service import tehran_today

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/pdf", response_class=Response)
def get_pdf(
    type: str = Query("weekly", description="نوع گزارش: daily/weekly/monthly"),
    date: dt.date | None = Query(None, description="تاریخ گزارش روزانه"),
    week_start: dt.date | None = Query(None, description="شنبه هفته گزارش هفتگی"),
    year: int | None = Query(None, ge=1300, le=1500, description="سال جلالی (ماهانه)"),
    month: int | None = Query(None, ge=1, le=12, description="ماه جلالی (ماهانه)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    """خروجی PDF گزارش (AT-25)."""
    content, filename = export_pdf(db, user, type, week_start, date, year, month)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/excel", response_class=Response)
def get_excel(
    type: str = Query("full", description="نوع خروجی (در نسخه ۱: کامل)"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    content, filename = export_excel(db, user)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/json", response_class=Response)
def get_json(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Response:
    """خروجی کامل JSON — مالکیت داده (AT-26)."""
    content, filename = export_json(db, user)
    return Response(
        content=content,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
