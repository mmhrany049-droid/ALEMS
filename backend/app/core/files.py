"""مدیریت فایل — File Management Module (کاتالوگ ماژول‌ها §3).

مسئولیت‌ها:
- مسیرهای استاندارد پروژه: data · backups · exports · imports
- خواندن و نوشتن JSON (فرمت باز — NFR-06)
- مدیریت فایل‌های خروجی

این ماژول مرجع یگانه مسیرهای استاندارد است؛ سایر ماژول‌ها مستقیماً
مسیر نهایی نمی‌سازند و از همین‌جا می‌گیرند.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings


def data_dir() -> Path:
    """پوشه داده برنامه (پایگاه داده و فایل‌های runtime)."""
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings.data_dir


def backups_dir() -> Path:
    """پوشه پشتیبان‌ها."""
    settings.backups_dir.mkdir(parents=True, exist_ok=True)
    return settings.backups_dir


def exports_dir() -> Path:
    """پوشه خروجی‌ها (PDF/Excel/JSON)."""
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    return settings.exports_dir


def imports_dir() -> Path:
    """پوشه فایل‌های ورودی (کتاب‌های JSON)."""
    settings.imports_dir.mkdir(parents=True, exist_ok=True)
    return settings.imports_dir


def ensure_standard_dirs() -> dict[str, Path]:
    """ایجاد همه مسیرهای استاندارد — در راه‌اندازی برنامه فراخوانی می‌شود."""
    return {
        "data": data_dir(),
        "backups": backups_dir(),
        "exports": exports_dir(),
        "imports": imports_dir(),
    }


# ---------- خواندن و نوشتن JSON ----------

def read_json(path: str | Path) -> dict:
    """خواندن فایل JSON با پیام خطای فارسی."""
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"فایل یافت نشد: {target.name}")
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"فایل «{target.name}» یک JSON معتبر نیست.") from exc


def write_json(path: str | Path, payload: dict, *, indent: int = 2) -> Path:
    """نوشتن JSON با فرمت باز و فارسی‌ساز (ensure_ascii=False)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )
    return target


def write_binary(path: str | Path, content: bytes) -> Path:
    """نوشتن فایل باینری (PDF/Excel/Backup)."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target
