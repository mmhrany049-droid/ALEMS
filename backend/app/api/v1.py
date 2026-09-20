"""API v1 — single router aggregating all module routers (doc 06, base /api/v1).

Each module router is defined in its module's router.py (doc 03 §3.3).
In phase 0 the routers are empty; endpoints land as their phases complete.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.modules.academic.router import router as academic_router
from app.modules.activity.router import router as activity_router
from app.modules.analytics.router import router as analytics_router
from app.modules.backup.router import router as backup_router
from app.modules.exam.router import router as exam_router
from app.modules.export.router import router as export_router
from app.modules.identity.router import router as identity_router
from app.modules.planning.router import router as planning_router
from app.modules.report.router import router as report_router
from app.modules.review.router import router as review_router
from app.modules.rewards.router import router as rewards_router
from app.modules.settings.router import router as settings_router
from app.modules.student.router import router as student_router

api_router = APIRouter()

api_router.include_router(identity_router)
api_router.include_router(student_router)
api_router.include_router(settings_router)
api_router.include_router(academic_router)
api_router.include_router(activity_router)
api_router.include_router(review_router)
api_router.include_router(planning_router)
api_router.include_router(exam_router)
api_router.include_router(analytics_router)
api_router.include_router(report_router)
api_router.include_router(export_router)
api_router.include_router(rewards_router)
api_router.include_router(backup_router)
