"""Motivation (Rewards & Behavior) — FastAPI router (mounted under /api/v1 by app.api.v1).

Points ledger append-only، streak شمسی، badge seed (OD4: ۸ تا ۱۲)، habit advice بعد از ۳۰ روز، procrastination aid (doc 13)

مسیرها (doc 06):
#   GET /rewards/summary
#   GET /rewards/badges

فیلد می‌شود در: فاز ۷
"""
from fastapi import APIRouter

router = APIRouter(tags=["rewards"])
