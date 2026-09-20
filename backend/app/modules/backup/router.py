"""Backup & Restore — router (doc 06 §Backup، V2-S01/S02)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.backup import service
from app.modules.backup.schemas import BackupCreateIn, BackupRestoreIn
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["backup"])


@router.post("/backup/create")
def create_backup(
    payload: BackupCreateIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> dict:
    meta = service.create_backup(db, student, label=payload.label, password=payload.password)
    db.commit()
    return ok(data=meta, meta={"message_fa": "فایل پشتیبان ساخته شد."})


@router.get("/backup/list")
def list_backups(
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> dict:
    return ok(service.list_backups())


@router.post("/backup/restore")
def restore_backup(
    payload: BackupRestoreIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
) -> dict:
    # V2-S02: confirm!==true → 422 (داخل service) | V2-S01: چرخه کامل create→restore
    # اول تراکنش خواندنِ auth آزاد شود تا swap بی‌قفل انجام شود (SQLite تک‌نویسنده)
    db.rollback()
    data = service.restore_backup(payload)
    return ok(data=data, meta={"message_fa": data["message_fa"]})


@router.get("/backup/download/{backup_id}")
def download_backup(
    backup_id: str,
    student: Student = Depends(get_current_student),
) -> FileResponse:
    # فایل خام (مثل export) — نه envelope
    return service.download_response(backup_id)
