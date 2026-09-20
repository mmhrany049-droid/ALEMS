"""Backup & Restore — pure domain rules, NO I/O (doc 03 §3.1، doc 04، doc 06 §Backup).

id = «{UTC:%Y%m%d-%H%M%S}-{4hex}» → نام فایل alems-backup-{id}.zip (+ sidecar .json برای
list بدون باز کردن zip). retention: نگه‌داشتن MAX_BACKUPS مورد آخر (doc 04: دستی، خودکار، AES).
"""
from __future__ import annotations

import datetime as dt
import re
import secrets

ID_RE = re.compile(r"^\d{8}-\d{6}-[0-9a-f]{4}$")
FILE_PREFIX = "alems-backup-"
MAX_BACKUPS = 20  # retention — قدیمی‌ترها در create پاک می‌شوند


def make_backup_id(now_utc: dt.datetime) -> str:
    return f"{now_utc:%Y%m%d-%H%M%S}-{secrets.token_hex(2)}"


def is_safe_id(bid: str) -> bool:
    """جلوگیری از path traversal — فقط الگوی id خودمان."""
    return bool(ID_RE.match(bid or ""))


def backup_filename(bid: str) -> str:
    return f"{FILE_PREFIX}{bid}.zip"


def sidecar_filename(bid: str) -> str:
    return f"{FILE_PREFIX}{bid}.json"


def prune_entries(entries: list[tuple[float, str]], keep: int = MAX_BACKUPS) -> list[tuple[float, str]]:
    """(mtime, id)ها صعودی (قدیمی اول)؛ مواردی که باید حذف شوند برمی‌گردند."""
    if len(entries) <= keep:
        return []
    return sorted(entries)[: len(entries) - keep]


# پیام‌های خطای فارسی (قید ۷)
MSG_CONFIRM_REQUIRED = (
    "برای بازیابی باید confirm را true بفرستی — این عملیات کل دادهٔ جاری را با فایل پشتیبان جایگزین می‌کند."
)
MSG_NOT_FOUND = "فایل پشتیبان پیدا نشد."
MSG_PASSWORD_REQUIRED = "این فایل پشتیبان رمز دارد — password را بفرست."
MSG_BAD_PASSWORD = "رمز فایل پشتیبان اشتباه است."
MSG_CORRUPT = "فایل پشتیبان سالم نیست (بررسی یکپارچگی ناموفق)."
MSG_RESTORED = "بازیابی کامل انجام شد — دادهٔ جاری با فایل پشتیبان جایگزین شد."
