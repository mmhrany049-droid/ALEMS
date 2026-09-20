"""Planning & Capacity & Today Hub — FastAPI router (mounted under /api/v1 by app.api.v1).

تقویم شمسی، اهداف، time blocks، ظرفیت واقعی، generate-week (pipeline ثابت)، Today Hub، priority، recommendation، recovery، manual override (doc 11)

مسیرها (doc 06):
#   GET/POST /goals
#   GET/PUT /time-blocks
#   GET/PUT /plans/{date}
#   POST /plans/generate-week
#   GET /today
#   GET /capacity?date=
#   POST /school-override
#   GET /recommendations/today
#   GET /priority/week
#   POST /recommendations/{id}/respond

فیلد می‌شود در: فاز ۵
"""
from fastapi import APIRouter

router = APIRouter(tags=["planning"])
