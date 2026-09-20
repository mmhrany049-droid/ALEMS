"""Configuration — ALEMS 2.0.

Env (phase-0 spec + doc 03):
    APP_NAME=ALEMS
    APP_VERSION=2.0.0
    HOST=127.0.0.1
    PORT=8010
    DATABASE_URL=sqlite:///./data/alems.db
    TIMEZONE=Asia/Tehran

Doc sources:
- doc 03 §3.2  stack, default ports (backend 8010 / frontend 5173)
- doc 03 §3.5  timezone Asia/Tehran, week 0=Saturday..6=Friday
- doc 02 NFR-4 backend default port 8010
- doc 18 OD2   SQLite by default, PostgreSQL via connection string
- doc 04        policy settings live in the settings module (phase 1) — infra only here
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/  (…/app/core/config.py -> parents[2])
BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]

# Default DB: backend/data/alems.db — identical to `sqlite:///./data/alems.db`
# when uvicorn is run from backend/ (phase-0 spec), but cwd-independent.
_DEFAULT_DB = f"sqlite:///{(BACKEND_ROOT / 'data' / 'alems.db').as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(BACKEND_ROOT / ".env"), extra="ignore")

    # app (phase-0 spec env names)
    APP_NAME: str = "ALEMS"
    APP_VERSION: str = "2.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8010
    FRONTEND_PORT: int = 5173

    # SQLite (WAL) by default; DATABASE_URL=postgresql://… for PostgreSQL (OD2)
    DATABASE_URL: str = _DEFAULT_DB

    # doc 03 §3.5 — calendar & time: stored UTC, displayed Jalali
    TIMEZONE: str = "Asia/Tehran"
    WEEK_START: int = 0  # 0=Saturday … 6=Friday

    # doc 03 folder layout — file management
    DATA_DIR: Path = BACKEND_ROOT / "data"
    BACKUPS_DIR: Path = BACKEND_ROOT / "backups"
    EXPORTS_DIR: Path = BACKEND_ROOT / "exports"
    IMPORTS_DIR: Path = BACKEND_ROOT / "imports"

    # doc 03 §3.6 — security (consumed by identity module, phase 1)
    SECRET_KEY: str = "alems-dev-secret-change-me"
    ACCESS_TOKEN_TTL_MINUTES: int = 720

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def app_name(self) -> str:
        return self.APP_NAME

    @property
    def app_version(self) -> str:
        return self.APP_VERSION

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def timezone(self) -> str:
        return self.TIMEZONE

    @property
    def backend_port(self) -> int:
        return self.PORT

    @property
    def data_dir(self) -> Path:
        return Path(self.DATA_DIR)

    @property
    def backups_dir(self) -> Path:
        return Path(self.BACKUPS_DIR)

    @property
    def exports_dir(self) -> Path:
        return Path(self.EXPORTS_DIR)

    @property
    def imports_dir(self) -> Path:
        return Path(self.IMPORTS_DIR)


@lru_cache
def get_settings() -> Settings:
    return Settings()
