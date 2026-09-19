"""روتر تنظیمات — /api/v1/settings"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.modules.settings.service import all_settings, update_settings
from app.shared.response import ok

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=dict)
def get_settings(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> dict:
    """تنظیمات برنامه (شامل سیاست‌های دامنه)."""
    return ok(all_settings(db))


@router.put("", response_model=dict)
def put_settings(
    payload: dict,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """به‌روزرسانی تنظیمات."""
    return ok(update_settings(db, payload))
