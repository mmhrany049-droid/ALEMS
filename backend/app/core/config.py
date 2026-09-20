"""Configuration — ALEMS 2.0.

Sources:
- doc 03 §3.2  stack, default ports (backend 8010 / frontend 5173)
- doc 03 §3.5  timezone Asia/Tehran, week 0=Saturday..6=Friday
- doc 02 NFR-4 backend default port 8010
- doc 18 OD2   SQLite by default, PostgreSQL via connection string (ALEMS_DATABASE_URL)
- doc 04        Settings module: policies live in DB (phase 1) — only infra defaults here
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/  (…/app/core/config.py -> parents[2])
BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ALEMS_",
        env_file=str(BACKEND_ROOT / ".env"),
        extra="ignore",
    )

    # app
    app_name: str = "ALEMS"
    app_version: str = "2.0.0"
    environment: str = "development"

    # doc 03 §3.2 — default ports (to avoid port issues on Windows)
    backend_port: int = 8010
    frontend_port: int = 5173

    # SQLite (WAL) by default; ALEMS_DATABASE_URL=postgresql://… for PostgreSQL (OD2)
    database_url: str = f"sqlite:///{(BACKEND_ROOT / 'data' / 'alems.db').as_posix()}"

    # doc 03 §3.5 — calendar & time: stored UTC, displayed Jalali
    timezone: str = "Asia/Tehran"
    week_start: int = 0  # 0=Saturday … 6=Friday

    # doc 03 folder layout — file management
    data_dir: Path = BACKEND_ROOT / "data"
    backups_dir: Path = BACKEND_ROOT / "backups"
    exports_dir: Path = BACKEND_ROOT / "exports"
    imports_dir: Path = BACKEND_ROOT / "imports"

    # doc 03 §3.6 — security (consumed by identity module, phase 1)
    secret_key: str = "alems-dev-secret-change-me"
    access_token_ttl_minutes: int = 720

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
