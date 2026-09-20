"""Settings — FastAPI router (mounted under /api/v1 by app.api.v1).

سیاست‌ها بدون hard-code: k جریمه کنکور، چرخه مرور [1,3,7,14]، سقف روزانه مرور، سکه (OD1) و ...

مسیرها (doc 06):
#   GET/PUT /settings

فیلد می‌شود در: فاز ۱
"""
from fastapi import APIRouter

router = APIRouter(tags=["settings"])
