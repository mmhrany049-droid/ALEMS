"""روتر ماژول تحلیل — /api/v1/analytics"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.analytics import service
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.shared.response import ok

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=dict)
def get_overview(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.overview(db, user.id, from_date, to_date))


@router.get("/by-subject", response_model=dict)
def get_by_subject(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.by_subject(db, user.id, from_date, to_date))


@router.get("/by-topic", response_model=dict)
def get_by_topic(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    subject_id: uuid.UUID | None = Query(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.by_topic(db, user.id, from_date, to_date, subject_id))


@router.get("/difficulty", response_model=dict)
def get_difficulty(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.by_difficulty(db, user.id, from_date, to_date))


@router.get("/mistake-types", response_model=dict)
def get_mistake_types(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(service.mistake_types(db, user.id, from_date, to_date))
