"""Student Profile, State & Taught Topics — FastAPI router (mounted under /api/v1 by app.api.v1).

پروفایل تحصیلی (پایه/رشته/هدف)، check-in + ابعاد state، تدریس‌شده‌ها با cascade (doc 08 §8.8)

مسیرها (doc 06):
#   GET/PUT /students/me
#   POST /students/me/checkin
#   GET /students/me/state
#   GET/PUT /students/me/taught-topics

فیلد می‌شود در: فاز ۱
"""
from fastapi import APIRouter

router = APIRouter(tags=["student"])
