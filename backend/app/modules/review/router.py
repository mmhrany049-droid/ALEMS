"""Review & Learning — FastAPI router (mounted under /api/v1 by app.api.v1).

صف مرور، چرخه ۱-۳-۷-۱۴، خوشه‌ای/تصادفی، Learning State چندبعدی، Weakness، Intervention (doc 10)

مسیرها (doc 06):
#   GET /reviews/queue
#   POST /reviews/{id}/complete
#   POST /reviews/{id}/postpone
#   POST /reviews/rebuild
#   GET /reviews/cluster-suggestion

فیلد می‌شود در: فاز ۴
"""
from fastapi import APIRouter

router = APIRouter(tags=["review"])
