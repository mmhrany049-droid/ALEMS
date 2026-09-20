"""Export — FastAPI router (mounted under /api/v1 by app.api.v1).

PDF (RTL فارسی) / Excel (openpyxl) / JSON کامل کاربر (doc 12 §12.5)

مسیرها (doc 06):
#   GET /export/pdf
#   GET /export/excel
#   GET /export/json

فیلد می‌شود در: فاز ۶
"""
from fastapi import APIRouter

router = APIRouter(tags=["export"])
