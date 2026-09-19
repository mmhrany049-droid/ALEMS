"""تست‌های پذیرش فاز ۰ — Foundation (AT-01 + ماژول‌های پایه)."""
from __future__ import annotations

import io

import pytest
from sqlalchemy import select


class TestHealth:
    def test_at_01_health_200(self, client):
        """/health باید ۲۰۰ و ساختار استاندارد برگرداند."""
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["status"] == "ok"

    def test_health_version_info(self, client):
        """Version Management: نسخه برنامه و schema در /health گزارش می‌شود."""
        from app.core.config import settings

        r = client.get("/health")
        body = r.json()
        assert body["app"] == settings.app_name
        assert body["version"] == settings.app_version
        assert body["schema_version"] == settings.schema_version

    def test_health_schema_state(self, client):
        """جدول schema_version ثبت شده و به‌روز است."""
        r = client.get("/health")
        schema = r.json()["database"]["schema"]
        assert schema["recorded"] is True
        assert schema["up_to_date"] is True
        assert settings_version() in schema["applied_versions"]

    def test_health_database_connected(self, client):
        r = client.get("/health")
        assert r.json()["database"]["connected"] is True


def settings_version() -> str:
    from app.core.config import settings

    return settings.schema_version


class TestFileManagement:
    """File Management Module — مسیرهای استاندارد و JSON."""

    def test_standard_dirs_exist(self):
        from app.core.files import ensure_standard_dirs

        dirs = ensure_standard_dirs()
        assert set(dirs.keys()) == {"data", "backups", "exports", "imports"}
        for path in dirs.values():
            assert path.exists()

    def test_json_roundtrip(self, tmp_path):
        from app.core.files import read_json, write_json

        payload = {"title": "کتاب تست", "count": 3, "items": ["الف", "ب"]}
        target = tmp_path / "sample.json"
        write_json(target, payload)
        assert read_json(target) == payload

    def test_read_json_invalid_persian_error(self, tmp_path):
        from app.core.files import read_json

        bad = tmp_path / "bad.json"
        bad.write_text("{معتبر نیست", encoding="utf-8")
        with pytest.raises(ValueError) as exc:
            read_json(bad)
        assert "JSON معتبر نیست" in str(exc.value)

    def test_read_json_missing_file(self, tmp_path):
        from app.core.files import read_json

        with pytest.raises(FileNotFoundError):
            read_json(tmp_path / "نیست.json")

    def test_write_binary(self, tmp_path):
        from app.core.files import write_binary

        target = write_binary(tmp_path / "sub" / "file.pdf", b"%PDF-test")
        assert target.read_bytes() == b"%PDF-test"


class TestVersionManagement:
    """Version Management Module — ثبت نسخه و state."""

    def test_schema_version_recorded(self):
        """نسخه جاری schema در پایگاه داده ثبت شده است."""
        from app.core.config import settings
        from app.core.versioning import SchemaVersion
        from tests.conftest import db_session

        db = db_session()
        try:
            row = db.get(SchemaVersion, settings.schema_version)
            assert row is not None
            assert row.applied_at is not None
        finally:
            db.close()

    def test_ensure_is_idempotent(self):
        """فراخوانی مکرر، رکورد تکراری نمی‌سازد."""
        from app.core.config import settings
        from app.core.versioning import SchemaVersion, ensure_schema_version_record
        from tests.conftest import db_session

        db = db_session()
        try:
            assert ensure_schema_version_record(db) is False  # قبلاً ثبت شده
            count = len(list(db.scalars(
                select(SchemaVersion).where(SchemaVersion.version == settings.schema_version)
            )))
            assert count == 1
        finally:
            db.close()

    def test_version_info_shape(self):
        from app.core.versioning import version_info

        info = version_info()
        assert {"app", "version", "schema_version", "timezone", "language"} <= set(info)
        assert info["timezone"] == "Asia/Tehran"


class TestCoreSystem:
    """Core System Module — Event Bus و لاگ."""

    def test_event_bus_subscribe_emit(self):
        from app.core.events import EventBus

        bus = EventBus()
        received: list[dict] = []
        bus.subscribe("test.event", received.append)
        bus.emit("test.event", {"value": 42})
        assert received == [{"value": 42}]

    def test_event_bus_broken_listener_does_not_break_emitter(self):
        """خطای شنونده نباید مسیر اصلی را بشکند (اصل Event Bus)."""
        from app.core.events import EventBus

        bus = EventBus()

        def broken(_payload: dict) -> None:
            raise RuntimeError("شنونده خراب")

        received: list[dict] = []
        bus.subscribe("test.event", broken)
        bus.subscribe("test.event", received.append)
        bus.emit("test.event", {"ok": True})  # نباید exception بدهد
        assert received == [{"ok": True}]

    def test_settings_defaults(self):
        from app.core.config import settings

        assert settings.timezone == "Asia/Tehran"
        assert settings.language == "fa"
        assert settings.database_url.startswith("sqlite:///")

    def test_validation_error_persian_envelope(self, client):
        """مدیریت خطای پایه: خطای اعتبارسنجی با پاکت استاندارد و پیام فارسی."""
        r = client.post("/api/v1/auth/register", json={"username": "x", "password": "1"})
        assert r.status_code == 422
        body = r.json()
        assert body["success"] is False
        assert body["error"]["code"] == "VALIDATION_ERROR"
        assert any("\u0600" <= ch <= "\u06FF" for ch in body["error"]["message"])

    def test_unknown_route_persian(self, client):
        """مسیر ناشناخته هم پاسخ استاندارد دارد."""
        r = client.get("/api/v1/چنین-مسیری-نیست")
        assert r.status_code == 404
