"""ALEMS 2.0 — FastAPI application factory.

Phase 0 outputs (doc 14 + phase-0 spec):
- app structure + DB (SQLite WAL) + Alembic
- GET /health and GET /api/v1/health (envelope doc 06)
- default port 8010, host 127.0.0.1 (overridable)
- Persian-friendly startup log with version + paths

Schema is managed by Alembic ONLY (doc 05).
"""
from __future__ import annotations

import datetime as dt
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.files import ensure_directories
from app.core.jalali import TEHRAN, today_jalali
from app.core.versioning import (
    APP_VERSION,
    SCHEMA_VERSION,
    get_meta_value,
    init_meta,
    schema_version_from_alembic,
)
from app.db.session import get_engine, session_scope
from app.modules.review.service import register_event_consumers
from app.modules.rewards import service as rewards_service
from app.shared.envelope import ok, register_envelope_handlers

logger = logging.getLogger("alems")


def _setup_logging() -> None:
    """فارسی-دوست logging: UTF-8, one clear line per record."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-5s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_directories(settings)
    with session_scope() as db:
        init_meta(db)
        rewards_service.ensure_badge_seed(db)  # doc 13.3 — seed نشان‌ها (OD4: ۸ تا ۱۲)
    # doc 03 §3.4 — مصرف‌کنندگان رویداد: test finish/past → review rebuild + learning states
    register_event_consumers()
    # doc 03 §3.4 — rewards هم مصرف‌کننده رویدادهاست (points ledger، فاز ۷)
    rewards_service.register_event_consumers()
    # doc 04 — پشتیبان خودکار در startup اگر auto_backup روشن باشد (فاز 8)
    from app.modules.backup.service import maybe_auto_backup
    maybe_auto_backup()
    logger.info(
        "%s نسخه %s راه‌اندازی شد — backend :%d | DB: %s",
        settings.app_name,
        settings.app_version,
        settings.backend_port,
        settings.database_url,
    )
    logger.info(
        "مسیرها — data: %s | backups: %s | exports: %s | imports: %s",
        settings.data_dir,
        settings.backups_dir,
        settings.exports_dir,
        settings.imports_dir,
    )
    yield
    get_engine().dispose()


def _health_payload() -> dict:
    settings = get_settings()
    now_utc = dt.datetime.now(dt.timezone.utc)
    today = today_jalali()
    try:
        with session_scope() as db:
            alembic_rev = schema_version_from_alembic(db)
            app_version = get_meta_value(db, "app_version", APP_VERSION)
            schema_version = get_meta_value(db, "schema_version", SCHEMA_VERSION)
    except Exception:  # DB not migrated yet — still answer, flag db state
        alembic_rev = "no-schema"
        app_version, schema_version = APP_VERSION, SCHEMA_VERSION
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": app_version,
        "app_version": app_version,
        "schema_version": schema_version,
        "alembic_revision": alembic_rev,
        "db": {"type": "sqlite" if settings.is_sqlite else "postgresql"},
        "now_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "now_tehran": now_utc.astimezone(TEHRAN).strftime("%Y-%m-%dT%H:%M:%S+03:30"),
        "today_jalali": today.format(),
        "today_jalali_fa": today.format_long_fa(),
        "week_start": "saturday",
        "timezone": settings.timezone,
    }


def create_app() -> FastAPI:
    _setup_logging()
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.app_name} {APP_VERSION}",
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    register_envelope_handlers(app)

    # CORS for Vite dev (doc 03 §3.2) — production path is the Vite proxy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            f"http://localhost:{settings.FRONTEND_PORT}",
            f"http://127.0.0.1:{settings.FRONTEND_PORT}",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def health() -> JSONResponse:  # noqa: F811 — shared by both routes
        return JSONResponse(content=ok(data=_health_payload(), meta={"port": settings.backend_port}))

    app.get("/health", tags=["infra"])(health)
    app.get("/api/v1/health", tags=["infra"])(health)

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
