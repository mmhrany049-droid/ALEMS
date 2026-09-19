"""سرویس پشتیبان‌گیری — Backup دستی/خودکار، فهرست، بازگردانی، دانلود.

- Backup با API استاندارد SQLite انجام می‌شود تا فایل همیشه consistent باشد (قانون ۸.۶).
- رمزنگاری اختیاری با رمز کاربر (pyzipper — AES).
"""
from __future__ import annotations

import io
import json
import re
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.files import backups_dir
from app.shared.exceptions import NotFoundError, ValidationError

NAME_RE = re.compile(r"^alems-backup-\d{8}-\d{6}(\.db|\.zip)$")


def _db_path() -> Path:
    return Path(settings.database_url.replace("sqlite:///", ""))


def create_backup(*, encrypted: bool = False, password: str | None = None) -> dict:
    """ایجاد پشتیبان جدید — کپی consistent از پایگاه داده."""
    now = datetime.now()
    stamp = now.strftime("%Y%m%d-%H%M%S")
    db_path = _db_path()
    raw_path = backups_dir() / f"alems-backup-{stamp}.db"

    # کپی امن با sqlite backup API (سازگار حتی هنگام استفاده)
    src = sqlite3.connect(str(db_path))
    dst = sqlite3.connect(str(raw_path))
    with dst:
        src.backup(dst)
    src.close()
    dst.close()

    if encrypted and password:
        final_name = f"alems-backup-{stamp}.zip"
        final_path = backups_dir() / final_name
        import pyzipper

        with pyzipper.AESZipFile(final_path, "w", compression=pyzipper.ZIP_DEFLATED,
                                 encryption=pyzipper.WZ_AES) as zf:
            zf.setpassword(password.encode("utf-8"))
            zf.write(raw_path, arcname=raw_path.name)
        raw_path.unlink()
    else:
        final_name = raw_path.name
        final_path = raw_path

    return {
        "id": final_name,
        "filename": final_name,
        "size_bytes": final_path.stat().st_size,
        "created_at": now.isoformat(),
        "encrypted": bool(encrypted and password),
    }


def has_backup_today() -> bool:
    """آیا امروز (بر اساس پیشوند نام) پشتیبانی ساخته شده است؟"""
    prefix = datetime.now().strftime("%Y%m%d")
    return any(backups_dir().glob(f"alems-backup-{prefix}-*.*"))


def maybe_auto_backup() -> dict | None:
    """پشتیبان خودکار — حداکثر یک‌بار در روز (قانون ۸.۷).

    اگر کلید general.auto_backup_enabled در تنظیمات فعال (پیش‌فرض) باشد
    و امروز پشتیبانی ساخته نشده باشد، یک پشتیبان می‌سازد؛ در غیر این صورت None.
    """
    from app.db.session import SessionLocal
    from app.modules.settings.service import KEY_GENERAL, get_setting

    db = SessionLocal()
    try:
        general = get_setting(db, KEY_GENERAL) or {}
    finally:
        db.close()
    if not general.get("auto_backup_enabled", True):
        return None
    if has_backup_today():
        return None
    return create_backup()


def list_backups() -> list[dict]:
    """فهرست پشتیبان‌های موجود."""
    result = []
    for path in sorted(backups_dir().glob("alems-backup-*"), reverse=True):
        if not NAME_RE.match(path.name):
            continue
        result.append({
            "id": path.name,
            "filename": path.name,
            "size_bytes": path.stat().st_size,
            "created_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "encrypted": path.suffix == ".zip",
        })
    return result


def get_backup_path(backup_id: str) -> Path:
    """مسیر فایل پشتیبان با اعتبارسنجی نام (جلوگیری از path traversal)."""
    if not NAME_RE.match(backup_id):
        raise NotFoundError("پشتیبان مورد نظر یافت نشد.")
    path = backups_dir() / backup_id
    if not path.exists():
        raise NotFoundError("پشتیبان مورد نظر یافت نشد.")
    return path


def restore_backup(backup_id: str, *, mode: str = "replace",
                   password: str | None = None, confirm: bool = False) -> dict:
    """بازگردانی پشتیبان — با تأیید دومرحله‌ای و هشدار جایگزینی کامل (قانون ۸.۶)."""
    if mode != "replace":
        raise ValidationError("در نسخه ۱ فقط حالت جایگزینی کامل پشتیبانی می‌شود (ادغام در نسخه‌های بعد).")
    if not confirm:
        raise ValidationError(
            "بازگردانی، تمام داده‌های فعلی را با محتوای پشتیبان جایگزین می‌کند. "
            "برای تأیید، مقدار confirm=true را ارسال کنید."
        )
    source = get_backup_path(backup_id)
    db_path = _db_path()

    tmp_path = backups_dir() / f".restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
    if source.suffix == ".zip":
        import pyzipper

        try:
            with pyzipper.AESZipFile(source) as zf:
                if password:
                    zf.setpassword(password.encode("utf-8"))
                inner = [n for n in zf.namelist() if n.endswith(".db")][0]
                with zf.open(inner) as f_in, open(tmp_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        except (RuntimeError, pyzipper.core.ZipCryptoError if hasattr(pyzipper, "core") else RuntimeError):
            raise ValidationError("رمز عبور پشتیبان رمزنگاری‌شده اشتباه یا لازم است.")
        except Exception as exc:  # noqa: BLE001
            raise ValidationError("بازکردن فایل پشتیبان ناموفق بود: فایل معتبر نیست.") from exc
    else:
        shutil.copyfile(source, tmp_path)

    # اعتبارسنجی فایل به عنوان SQLite معتبر
    check = sqlite3.connect(str(tmp_path))
    try:
        check.execute("SELECT count(*) FROM users")
    except sqlite3.DatabaseError as exc:
        check.close()
        tmp_path.unlink(missing_ok=True)
        raise ValidationError("فایل پشتیبان معتبر نیست.") from exc
    finally:
        check.close()

    # تعویض امن فایل دیتابیس
    for suffix in ("-wal", "-shm"):
        Path(str(db_path) + suffix).unlink(missing_ok=True)
    shutil.move(str(tmp_path), str(db_path))
    return {"restored": backup_id, "mode": "replace"}


def backup_json_bytes(backup_id: str) -> bytes:
    """محتوای باینری پشتیبان برای دانلود."""
    return get_backup_path(backup_id).read_bytes()
