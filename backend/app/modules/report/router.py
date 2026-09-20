"""Report — FastAPI router (mounted under /api/v1 by app.api.v1).

گزارش روزانه/هفتگی/ماهانه (doc 12 §12.5)

مسیرها (doc 06):
#   GET /reports/daily
#   GET /reports/weekly
#   GET /reports/monthly

فیلد می‌شود در: فاز ۶
"""
from fastapi import APIRouter

router = APIRouter(tags=["report"])
