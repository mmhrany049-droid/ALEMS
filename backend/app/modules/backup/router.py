"""Backup & Restore — FastAPI router (mounted under /api/v1 by app.api.v1).

دستی/خودکار، AES اختیاری، بدون از دست رفتن داده (doc 04, doc 06 §Backup, AT V2-S01/S02)

مسیرها (doc 06):
#   POST /backup/create
#   GET /backup/list
#   POST /backup/restore
#   GET /backup/download/{id}

فیلد می‌شود در: فاز ۸
"""
from fastapi import APIRouter

router = APIRouter(tags=["backup"])
