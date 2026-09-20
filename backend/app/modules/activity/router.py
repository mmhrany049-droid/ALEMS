"""Activity & Test Engine — FastAPI router (mounted under /api/v1 by app.api.v1).

Test Record append-only، Test Engine (range/parity/timed)، time tracking، past import با NOT_ENTERED، تیک‌ها، دفترچه خطا (doc 09)

مسیرها (doc 06):
#   POST /test-sessions
#   POST /test-sessions/{id}/records
#   POST /test-sessions/{id}/finish
#   POST /tests/past-import
#   GET /test-engine/preview

فیلد می‌شود در: فاز ۳
"""
from fastapi import APIRouter

router = APIRouter(tags=["activity"])
