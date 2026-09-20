"""Backup & Restore — services (doc 04 «دستی، خودکار، AES»، doc 06 §Backup، V2-S01/S02).

create: snapshot یکپارچه SQLite (sqlite3 backup API روی WAL) + meta → zip (AES اختیاری با
pyzipper) + sidecar json برای list سریع. restore: confirm اجباری (V2-S02) → extract →
PRAGMA integrity_check → جایگزینی فایل DB (engine.dispose اول تا دسته‌ای فایل آزاد شود).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import sqlite3
import tempfile
import zipfile
from pathlib import Path
from typing import Any

import pyzipper
from fastapi.exceptions import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.jalali import gregorian_to_jalali
from app.db.session import get_engine
from app.modules.backup import domain
from app.modules.student.models import Student

logger = logging.getLogger("alems.backup")

TZ_TEHRAN = dt.timezone(dt.timedelta(hours=3, minutes=30))


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _jalali_str(d: dt.date) -> str:
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def _db_path() -> Path:
    url = get_engine().url
    if url.drivername.startswith("sqlite"):
        return Path(str(url.database))
    raise HTTPException(status_code=501, detail="پشتیبان‌گیری فقط برای SQLite فعال است.")


def _alembic_revision(db: Session) -> str | None:
    try:
        return db.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    except Exception:  # pragma: no cover
        return None


def _snapshot_db(dest: Path) -> None:
    """snapshot سازگار از DB زنده (WAL-aware) با sqlite3 backup API."""
    src = sqlite3.connect(str(_db_path()))
    try:
        dst = sqlite3.connect(str(dest))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


# --- create -----------------------------------------------------------------------------------

def _build_meta(bid: str, label: str | None, encrypted: bool, db_bytes: int,
                alembic: str | None, student_id: str | None) -> dict[str, Any]:
    now = _utcnow()
    tehran = now.astimezone(TZ_TEHRAN)
    return {
        "id": bid,
        "app": get_settings().app_name,
        "version": get_settings().app_version,
        "alembic_revision": alembic,
        "label": label,
        "encrypted": encrypted,
        "db_bytes": db_bytes,
        "student_id": student_id,
        "created_at": now.isoformat(),
        "created_at_jalali": _jalali_str(tehran.date()),
        "created_at_local": tehran.strftime("%Y-%m-%d %H:%M"),
    }


def create_backup(db: Session, student: Student | None, label: str | None = None,
                  password: str | None = None) -> dict[str, Any]:
    settings = get_settings()
    bdir: Path = settings.backups_dir
    bdir.mkdir(parents=True, exist_ok=True)
    bid = domain.make_backup_id(_utcnow())
    for _ in range(8):  # تصادف id در همان ثانیه → بازتولید
        zip_path = bdir / domain.backup_filename(bid)
        if not zip_path.exists():
            break
        bid = domain.make_backup_id(_utcnow())
    sidecar = bdir / domain.sidecar_filename(bid)

    with tempfile.TemporaryDirectory(prefix="alems-bk-") as tmp:
        snap = Path(tmp) / "alems.db"
        _snapshot_db(snap)
        db_bytes = snap.stat().st_size
        encrypted = bool(password)
        if encrypted:
            with pyzipper.AESZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED,
                                     encryption=pyzipper.WZ_AES) as z:
                z.setpassword(password.encode("utf-8"))  # type: ignore[union-attr]
                z.write(snap, "alems.db")
        else:
            with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
                z.write(snap, "alems.db")

    meta = _build_meta(bid, label, encrypted, db_bytes, _alembic_revision(db),
                       student.id if student else None)
    sidecar.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    _prune(bdir)
    logger.info("backup created id=%s encrypted=%s bytes=%s", bid, encrypted, zip_path.stat().st_size)
    return _meta_out(bid, zip_path, meta)


def _prune(bdir: Path) -> None:
    entries = sorted(
        ((f.stat().st_mtime, f.name[len(domain.FILE_PREFIX):-4])
         for f in bdir.glob(f"{domain.FILE_PREFIX}*.zip")
         if domain.is_safe_id(f.name[len(domain.FILE_PREFIX):-4])),
    )  # mtime → ترتیب واقعی ساخت (idها در یک ثانیه ترتیب رشته‌ای ندارند)
    for _mtime, old in domain.prune_entries(entries, keep=domain.MAX_BACKUPS):
        for f in (bdir / domain.backup_filename(old), bdir / domain.sidecar_filename(old)):
            f.unlink(missing_ok=True)


def _meta_out(bid: str, zip_path: Path, meta: dict[str, Any]) -> dict[str, Any]:
    return {**meta, "size_bytes": zip_path.stat().st_size if zip_path.exists() else None}


# --- list / download ----------------------------------------------------------------------------

def list_backups() -> dict[str, Any]:
    bdir = get_settings().backups_dir
    items = []
    if bdir.exists():
        zips = sorted(bdir.glob(f"{domain.FILE_PREFIX}*.zip"),
                      key=lambda f: (f.stat().st_mtime, f.name), reverse=True)  # جدیدترین اول
        for z in zips:
            bid = z.name[len(domain.FILE_PREFIX):-4]
            if not domain.is_safe_id(bid):
                continue
            sc = bdir / domain.sidecar_filename(bid)
            meta: dict[str, Any] = {"id": bid}
            if sc.exists():
                try:
                    meta = json.loads(sc.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    pass
            items.append(_meta_out(bid, z, meta))
    return {"items": items, "count": len(items), "retention": domain.MAX_BACKUPS}


def download_response(bid: str):
    from fastapi.responses import FileResponse

    if not domain.is_safe_id(bid):
        raise HTTPException(status_code=404, detail=domain.MSG_NOT_FOUND)
    path = get_settings().backups_dir / domain.backup_filename(bid)
    if not path.exists():
        raise HTTPException(status_code=404, detail=domain.MSG_NOT_FOUND)
    return FileResponse(path, media_type="application/zip", filename=path.name)


# --- restore (V2-S01/S02) ------------------------------------------------------------------------

def restore_backup(payload) -> dict[str, Any]:
    if payload.confirm is not True:
        raise HTTPException(status_code=422, detail=domain.MSG_CONFIRM_REQUIRED)
    bid = payload.id
    if not domain.is_safe_id(bid):
        raise HTTPException(status_code=404, detail=domain.MSG_NOT_FOUND)
    bdir = get_settings().backups_dir
    zip_path = bdir / domain.backup_filename(bid)
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail=domain.MSG_NOT_FOUND)
    sc = bdir / domain.sidecar_filename(bid)
    meta: dict[str, Any] = {}
    if sc.exists():
        try:
            meta = json.loads(sc.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            meta = {}
    encrypted = bool(meta.get("encrypted"))

    with tempfile.TemporaryDirectory(prefix="alems-rs-") as tmp:
        tmpdir = Path(tmp)
        if encrypted:
            if not payload.password:
                raise HTTPException(status_code=422, detail=domain.MSG_PASSWORD_REQUIRED)
            try:
                with pyzipper.AESZipFile(zip_path) as z:
                    z.extractall(path=str(tmpdir), pwd=payload.password.encode("utf-8"))
            except RuntimeError as e:
                if "password" in str(e).lower() or "encrypted" in str(e).lower():
                    raise HTTPException(status_code=422, detail=domain.MSG_BAD_PASSWORD) from e
                raise HTTPException(status_code=422, detail=domain.MSG_CORRUPT) from e
        else:
            try:
                with zipfile.ZipFile(zip_path) as z:
                    z.extractall(path=str(tmpdir))
            except (zipfile.BadZipFile, RuntimeError) as e:
                raise HTTPException(status_code=422, detail=domain.MSG_BAD_PASSWORD if "encrypted" in str(e).lower() else domain.MSG_CORRUPT) from e

        restored_db = tmpdir / "alems.db"
        if not restored_db.exists():
            raise HTTPException(status_code=422, detail=domain.MSG_CORRUPT)
        revision = _verify_sqlite(restored_db)

        # جایگزینی محتوای DB زنده با sqlite3 backup API — inode عوض نمی‌شود و
        # قفل‌ها هماهنگ می‌مانند (اتصال‌های بازِ pool با dispose بسته می‌شوند؛
        # روتر قبل از این نقطه تراکنش auth را rollback کرده است).
        get_engine().dispose()
        dest = sqlite3.connect(str(_db_path()))
        try:
            src = sqlite3.connect(str(restored_db))
            try:
                src.backup(dest)
            finally:
                src.close()
        finally:
            dest.close()  # checkpoint WAL روی live

    logger.info("backup restored id=%s alembic=%s", bid, revision)
    return {
        "restored": {**meta, "id": bid},
        "alembic_revision": revision,
        "message_fa": domain.MSG_RESTORED,
    }


def _verify_sqlite(path: Path) -> str | None:
    con = sqlite3.connect(str(path))
    try:
        ok_row = con.execute("PRAGMA integrity_check").fetchone()
        if not ok_row or ok_row[0] != "ok":
            raise HTTPException(status_code=422, detail=domain.MSG_CORRUPT)
        try:
            row = con.execute("SELECT version_num FROM alembic_version").fetchone()
        except sqlite3.OperationalError:  # جدول alembic در snapshot نیست
            raise HTTPException(status_code=422, detail=domain.MSG_CORRUPT) from None
        return str(row[0]) if row else None
    except sqlite3.Error as e:
        raise HTTPException(status_code=422, detail=domain.MSG_CORRUPT) from e
    finally:
        con.close()


# --- خودکار (doc 04: دستی، خودکار، AES) -------------------------------------------------------------

def maybe_auto_backup() -> None:
    """اگر settings.auto_backup روشن باشد، در startup یک پشتیبان بدون رمز ساخته می‌شود."""
    from app.db.session import session_scope
    from app.modules.settings.service import get_all as get_settings_map

    try:
        with session_scope() as db:
            if not get_settings_map(db).get("auto_backup", False):
                return
            create_backup(db, None, label="خودکار (startup)")
    except Exception:  # pragma: no cover — startup هرگز نباید بشکند
        logger.exception("auto backup failed")
