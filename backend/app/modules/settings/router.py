"""Settings — FastAPI router (doc 06: GET/PUT /settings)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.settings import service
from app.modules.settings.schemas import SettingsUpdate
from app.shared.deps import get_current_user
from app.shared.envelope import ok

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ok(data=service.get_all(db))


@router.put("/settings")
def put_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = service.update(db, body)
    db.commit()
    return ok(data=data)
