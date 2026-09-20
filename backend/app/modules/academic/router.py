"""Academic Knowledge (Books & Import) — FastAPI router (mounted under /api/v1 by app.api.v1).

درخت دروس، منابع و کتاب، Import TOC-only و کامل، سوال + answer key نسخه‌دار، سختی/تگ/اهمیت، block_type (doc 09)

مسیرها (doc 06):
#   POST /resources/import-book
#   GET /resources/import-book/schema
#   GET /resources
#   GET /resources/{id}/tree
#   GET /subjects/...

فیلد می‌شود در: فاز ۲
"""
from fastapi import APIRouter

router = APIRouter(tags=["academic"])
