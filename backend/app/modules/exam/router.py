"""Exam Center & Scoring — FastAPI router (mounted under /api/v1 by app.api.v1).

mock | school_subject | free؛ planned/in_progress/finished/cancelled؛ درصد کنکوری (C - k*W)/T (doc 08 §8.1, doc 12 §12.2)

مسیرها (doc 06):
#   CRUD /exams
#   POST /exams/{id}/start
#   POST /exams/{id}/submit
#   GET /exams/{id}/result

فیلد می‌شود در: فاز ۶
"""
from fastapi import APIRouter

router = APIRouter(tags=["exam"])
