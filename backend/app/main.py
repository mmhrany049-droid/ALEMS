"""ALEMS 2.0 — FastAPI application factory.

Phase 0 outputs (doc 14):
- app structure + DB (SQLite WAL) + Alembic
- GET /health (envelope doc 06, Jalali date, versions)
- default port 8010 (doc 02 NFR-4) — see scripts/run.sh

Schema is managed by Alembic ONLY (doc 05).
"""
from __future__ import annotations

import datetime as dt

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
from app.db.session import get_db, get_engine, session_scope
from app.shared.envelope import ok, register_envelope_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    ensure_directories(settings)
    # record app + schema versions (idempotent)
    with session_scope() as db:
        init_meta(db)
    yield
    get_engine().dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=f"{settings.app_name} {APP_VERSION}",
        version=APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    register_envelope_handlers(app)

    # dev convenience only — the production path is the Vite proxy (doc 03 §3.2)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["infra"])
    def health() -> JSONResponse:
        now_utc = dt.datetime.now(dt.timezone.utc)
        today = today_jalali()
        alembic_rev = "unknown"
        try:
            with session_scope() as db:
                alembic_rev = schema_version_from_alembic(db)
                app_version = get_meta_value(db, "app_version", APP_VERSION)
                schema_version = get_meta_value(db, "schema_version", SCHEMA_VERSION)
        except Exception:  # DB not migrated yet — still answer, flag db state
            alembic_rev = "no-schema"
            app_version, schema_version = APP_VERSION, SCHEMA_VERSION
        return JSONResponse(
            content=ok(
                data={
                    "status": "ok",
                    "app": settings.app_name,
                    "app_version": app_version,
                    "schema_version": schema_version,
                    "alembic_revision": alembic_rev,
                    "db": {"type": "sqlite" if settings.is_sqlite else "postgresql"},
                    "now_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "now_tehran": now_utc.astimezone(TEHRAN).strftime("%Y-%m-%dT%H:%M:%S+03:30"),
                    "today_jalali": today.format(),
                    "today_jalali_fa": today.format_long_fa(),
                    "week_start": "saturday",
                    "timezone": "Asia/Tehran",
                },
                meta={"port": settings.backend_port},
            )
        )

    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
