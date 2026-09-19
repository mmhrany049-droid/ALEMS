"""پیکربندی تست‌ها — پایگاه داده جداگانه و ایزوله برای هر اجرا."""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

# تنظیم محیط قبل از import کردن app
_TMP_DB = Path(tempfile.mkdtemp()) / "alems-test.db"
os.environ["ALEMS_DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["ALEMS_SECRET_KEY"] = "test-secret-key"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.db.session import Base, engine  # noqa: E402


def db_session():
    """نشست مستقیم دیتابیس برای تست‌های زیرساختی."""
    from app.db.session import SessionLocal

    return SessionLocal()


@pytest.fixture(scope="session", autouse=True)
def _setup_db():
    """ساخت جداول + مقادیر پیش‌فرض یک‌بار برای کل جلسه تست."""
    from app.modules import models_registry  # noqa: F401 — ثبت همه مدل‌ها در metadata
    Base.metadata.create_all(bind=engine)
    from app.modules.seed import ensure_defaults
    from app.db.session import SessionLocal

    db = SessionLocal()
    try:
        ensure_defaults(db)
    finally:
        db.close()
    yield
    engine.dispose()


@pytest.fixture()
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_client(client: TestClient) -> TestClient:
    """کلاینت با کاربر ثبت‌شده و پروفایل کامل."""
    username = f"student_{uuid.uuid4().hex[:8]}"
    r = client.post("/api/v1/auth/register", json={
        "username": username, "password": "secret123", "full_name": "دانش‌آموز تست",
    })
    assert r.status_code == 200, r.text
    r = client.post("/api/v1/auth/login", json={
        "username": username, "password": "secret123",
    })
    assert r.status_code == 200, r.text
    token = r.json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})

    r = client.put("/api/v1/students/me", json={
        "full_name": "دانش‌آموز تست", "grade": "دوازدهم", "field": "ریاضی",
        "academic_year": "1404", "target_rank": 100, "target_major": "کامپیوتر",
    })
    assert r.status_code == 200, r.text
    client.headers["X-Test-User"] = username
    return client


def register_and_login(client: TestClient, username: str, password: str = "secret123") -> str:
    client.post("/api/v1/auth/register", json={"username": username, "password": password})
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    return r.json()["data"]["access_token"]
