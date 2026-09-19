"""مونتاژ روترهای نسخه ۱ — Base URL: /api/v1"""
from __future__ import annotations

from fastapi import APIRouter

from app.modules.academic.router import router as academic_router
from app.modules.activity.review_router import router as review_router
from app.modules.activity.router import router as activity_router
from app.modules.analytics.router import router as analytics_router
from app.modules.backup.router import router as backup_router
from app.modules.exam.router import router as exam_router
from app.modules.export.router import router as export_router
from app.modules.identity.router import router as identity_router
from app.modules.planning.router import router as planning_router
from app.modules.report.router import router as report_router
from app.modules.settings.router import router as settings_router
from app.modules.student.router import router as student_router

api_v1 = APIRouter(prefix="/api/v1")

api_v1.include_router(identity_router)
api_v1.include_router(student_router)
api_v1.include_router(academic_router)
api_v1.include_router(activity_router)
api_v1.include_router(review_router)
api_v1.include_router(planning_router)
api_v1.include_router(exam_router)
api_v1.include_router(analytics_router)
api_v1.include_router(report_router)
api_v1.include_router(export_router)
api_v1.include_router(backup_router)
api_v1.include_router(settings_router)
