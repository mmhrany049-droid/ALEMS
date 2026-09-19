"""تنظیمات مرکزی ALEMS — Core System Module"""
from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# مسیرهای استاندارد پروژه (File Management Module)
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
APP_DIR = BASE_DIR / "app"


class Settings(BaseSettings):
    """تنظیمات پایه برنامه — از متغیرهای محیطی قابل بازنویسی است."""

    model_config = SettingsConfigDict(env_prefix="ALEMS_", env_file=".env", extra="ignore")

    app_name: str = "ALEMS"
    app_version: str = "1.0.0"
    schema_version: str = "1.0.0"
    timezone: str = "Asia/Tehran"
    language: str = "fa"

    # پایگاه داده
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'alems.db'}"

    # امنیت
    secret_key: str = "alems-dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 14  # دو هفته — کاربرد آفلاین/محلی

    # مسیرهای استاندارد (File Management Module)
    data_dir: Path = BASE_DIR / "data"
    backups_dir: Path = BASE_DIR / "backups"
    exports_dir: Path = BASE_DIR / "exports"
    imports_dir: Path = BASE_DIR / "imports"

    debug: bool = True


settings = Settings()

for _d in (settings.data_dir, settings.backups_dir, settings.exports_dir, settings.imports_dir):
    _d.mkdir(parents=True, exist_ok=True)
