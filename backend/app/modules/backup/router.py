"""روتر ماژول پشتیبان‌گیری — /api/v1/backup"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db, engine
from app.modules.backup import service
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.shared.response import ok

router = APIRouter(prefix="/backup", tags=["backup"])


class BackupCreateIn(BaseModel):
    encrypted: bool = False
    password: str | None = Field(None, min_length=4, max_length=128,
                                 description="رمز پشتیبان (اختیاری)")


class BackupRestoreIn(BaseModel):
    backup_id: str
    mode: str = "replace"
    password: str | None = None
    confirm: bool = False


@router.post("/create", response_model=dict)
def post_create(
    payload: BackupCreateIn | None = None,
    user: User = Depends(current_user),
) -> dict:
    """ایجاد پشتیبان دستی (AT-27)."""
    payload = payload or BackupCreateIn()
    result = service.create_backup(encrypted=payload.encrypted, password=payload.password)
    return ok(result)


@router.get("/list", response_model=dict)
def get_list(user: User = Depends(current_user)) -> dict:
    return ok(service.list_backups())


@router.post("/restore", response_model=dict)
def post_restore(
    payload: BackupRestoreIn,
    user: User = Depends(current_user),
) -> dict:
    """بازگردانی — نیاز به تأیید دومرحله‌ای (AT-27)."""
    result = service.restore_backup(payload.backup_id, mode=payload.mode,
                                    password=payload.password, confirm=payload.confirm)
    return ok(result)


@router.get("/download/{backup_id}", response_class=Response)
def get_download(
    backup_id: str,
    user: User = Depends(current_user),
) -> Response:
    """دانلود فایل پشتیبان — انتقال داده بین دستگاه‌ها."""
    content = service.backup_json_bytes(backup_id)
    media = "application/zip" if backup_id.endswith(".zip") else "application/octet-stream"
    return Response(content=content, media_type=media,
                    headers={"Content-Disposition": f'attachment; filename="{backup_id}"'})
