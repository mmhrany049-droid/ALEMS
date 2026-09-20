"""Identity & Session & Permission — FastAPI router (mounted under /api/v1 by app.api.v1).

ثبت‌نام/ورود با bcrypt، JWT، نقش‌های student/advisor/parent/admin (doc 04, doc 06 §Auth)

مسیرها (doc 06):
#   POST /auth/register
#   POST /auth/login
#   POST /auth/logout
#   GET /auth/me

فیلد می‌شود در: فاز ۱
"""
from fastapi import APIRouter

router = APIRouter(tags=["identity"])
