"""تست‌های پشتیبان‌گیری — خودکار روزانه (قانون ۸.۷)، رمزنگاری و بازگردانی.

سند 08 §8.7: «Backup خودکار حداکثر یک‌بار در روز (قابل تغییر در تنظیمات)».
"""
from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from app.modules.backup import service as backup_mod
from app.modules.backup.service import (
    create_backup,
    has_backup_today,
    list_backups,
    maybe_auto_backup,
)


@pytest.fixture()
def backup_dir(tmp_path, monkeypatch):
    """هدایت مسیر پشتیبان‌ها به tmp — تا پشتیبان تست به پوشه واقعی نریزد."""
    d = tmp_path / "backups"
    d.mkdir()
    monkeypatch.setattr(backup_mod, "backups_dir", lambda: d)
    return d


@pytest.fixture()
def auto_enabled(monkeypatch):
    """کنترل کلید general.auto_backup_enabled بدون نوشتن در DB مشترک."""
    holder = {"general": {}}
    monkeypatch.setattr(
        "app.modules.settings.service.get_setting",
        lambda db, key: holder.get(key),
    )
    return holder


class TestAutoBackup:
    """پشتیبان خودکار — حداکثر یک‌بار در روز."""

    def test_first_call_creates(self, backup_dir, auto_enabled):
        result = maybe_auto_backup()
        assert result is not None
        assert result["filename"].startswith("alems-backup-")
        assert (backup_dir / result["filename"]).exists()

    def test_second_call_same_day_skipped(self, backup_dir, auto_enabled):
        first = maybe_auto_backup()
        assert first is not None
        assert maybe_auto_backup() is None
        assert len(list(backup_dir.glob("alems-backup-*"))) == 1

    def test_has_backup_today(self, backup_dir, auto_enabled):
        assert has_backup_today() is False
        create_backup()
        assert has_backup_today() is True

    def test_disabled_in_settings(self, backup_dir, auto_enabled):
        auto_enabled["general"] = {"auto_backup_enabled": False}
        assert maybe_auto_backup() is None
        assert list(backup_dir.glob("alems-backup-*")) == []

    def test_manual_backup_does_not_block_auto_same_day_is_fine(
        self, backup_dir, auto_enabled
    ):
        """اگر پشتیبان دستی امروز هست، خودکار لازم نیست (همان سهم روزانه)."""
        create_backup()
        assert maybe_auto_backup() is None


class TestBackupBasics:
    """پشتیبان دستی + رمزنگاری + فهرست."""

    def test_manual_backup_and_list(self, backup_dir):
        result = create_backup()
        assert result["encrypted"] is False
        rows = list_backups()
        assert any(r["filename"] == result["filename"] for r in rows)
        assert all("size_bytes" in r and "created_at" in r for r in rows)

    def test_encrypted_backup_is_zip(self, backup_dir):
        result = create_backup(encrypted=True, password="secret-رمز")
        assert result["encrypted"] is True
        assert result["filename"].endswith(".zip")
        path = backup_dir / result["filename"]
        assert path.read_bytes()[:2] == b"PK"  # امضای zip

    def test_restore_requires_confirm(self, backup_dir):
        result = create_backup()
        with pytest.raises(Exception) as exc:
            backup_mod.restore_backup(result["id"], confirm=False)
        assert "تأیید" in str(exc.value)

    def test_restore_replaces_data(self, backup_dir):
        """بازگردانی = جایگزینی کامل؛ پس از restore فایل DB معتبر است."""
        import sqlite3

        from app.core.config import settings as app_settings

        result = create_backup()
        backup_mod.restore_backup(result["id"], mode="replace", confirm=True)
        db_path = Path(str(app_settings.database_url).replace("sqlite:///", ""))
        conn = sqlite3.connect(str(db_path))
        tables = {
            r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        }
        conn.close()
        assert "students" in tables or "users" in tables  # schema سالم


def _unique_backup_dir(tmp_path: Path) -> Path:
    return tmp_path / f"bk_{uuid.uuid4().hex[:8]}"
