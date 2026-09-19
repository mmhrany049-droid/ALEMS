"""ALEMS — Academic Life & Exam Management System (Backend).

نقطه ورود FastAPI — پاکت پاسخ استاندارد و مدیریت خطاهای فارسی.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1 import api_v1
from app.core.config import settings
from app.core.events import event_bus
from app.core.logging import setup_logging

logger = logging.getLogger("alems")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    from app.modules.seed import ensure_defaults  # noqa: F401 — بارگذاری مقادیر پیش‌فرض
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    logger.info("ALEMS v%s راه‌اندازی شد", settings.app_version)
    yield
    logger.info("ALEMS خاموش شد")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # برنامه محلی/آفلاین است
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- مدیریت خطا با پاکت استاندارد و پیام فارسی ----------

def _fail(status: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"success": False, "data": None,
                 "error": {"code": code, "message": message, "details": details or {}}},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("خطای غیرمنتظره در %s", request.url.path)
    return _fail(500, "INTERNAL_ERROR", "خطای غیرمنتظره‌ای رخ داد. لطفاً دوباره تلاش کنید.")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = {}
    for err in exc.errors():
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        details[loc] = err.get("msg", "")
    return _fail(422, "VALIDATION_ERROR", "داده‌های ارسالی معتبر نیستند. لطفاً فیلدها را بررسی کنید.", details)


from app.shared.exceptions import AlemsError  # noqa: E402


@app.exception_handler(AlemsError)
async def alems_error_handler(request: Request, exc: AlemsError) -> JSONResponse:
    return _fail(exc.status_code, exc.code, exc.message, exc.details)


# ---------- مسیرهای پایه ----------

@app.get("/health")
def health() -> dict:
    """سلامت برنامه (AT-01)."""
    from app.db.session import engine

    db_ok = True
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
    return {
        "success": db_ok,
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "schema_version": settings.schema_version,
    }


app.include_router(api_v1)
