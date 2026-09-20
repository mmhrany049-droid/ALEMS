"""Analytics & Visualization & Explain — FastAPI router (mounted under /api/v1 by app.api.v1).

Coverage/Accuracy/Volume جدا (doc 08 §8.5)، برش‌های subject/topic/difficulty/error_type/time_bucket، explain پیشنهاد (doc 08 §8.10)

مسیرها (doc 06):
#   GET /analytics/overview
#   GET /analytics/by-subject|by-topic|difficulty|mistakes

فیلد می‌شود در: فاز ۶
"""
from fastapi import APIRouter

router = APIRouter(tags=["analytics"])
