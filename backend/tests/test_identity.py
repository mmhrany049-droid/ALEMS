"""تست‌های واحد فاز ۱ — User Identity · Session · Permission (AT-02، AT-03 + موارد بیشتر)."""
from __future__ import annotations

import uuid

import pytest


def _uname() -> str:
    return f"idn_{uuid.uuid4().hex[:8]}"


class TestRegister:
    """تست واحد ثبت‌نام."""

    def test_register_success(self, client):
        uname = _uname()
        r = client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["username"] == uname
        assert data["role"] in ("student", "admin")
        # امنیت: هش رمز هرگز در پاسخ نیست
        assert "password_hash" not in data
        assert "password" not in data

    def test_register_duplicate_persian_conflict(self, client):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/register", json={
            "username": uname, "password": "other-pass"})
        assert r.status_code == 409
        assert "قبلاً ثبت شده" in r.json()["error"]["message"]

    @pytest.mark.parametrize("bad_username", ["ab", "", "فارسی_نه", "has space", "x" * 65])
    def test_register_invalid_username(self, client, bad_username):
        r = client.post("/api/v1/auth/register", json={
            "username": bad_username, "password": "secret123"})
        assert r.status_code == 422
        body = r.json()
        assert body["success"] is False
        assert any("\u0600" <= ch <= "\u06FF" for ch in body["error"]["message"])

    @pytest.mark.parametrize("bad_password", ["12345", "", "x" * 129])
    def test_register_invalid_password(self, client, bad_password):
        r = client.post("/api/v1/auth/register", json={
            "username": _uname(), "password": bad_password})
        assert r.status_code == 422

    def test_register_with_full_name_creates_profile_stub(self, auth_client_factory):
        """full_name هنگام ثبت‌نام → پروفایل اولیه با نام (ناقص تا تکمیل پایه/رشته)."""
        client, uname = auth_client_factory(full_name="سارا تست")
        r = client.get("/api/v1/students/me")
        data = r.json()["data"]
        assert data["full_name"] == "سارا تست"
        assert data["is_complete"] is False  # پایه/رشته هنوز انتخاب نشده

    def test_bcrypt_hash_not_reversible(self):
        """هش رمز با bcrypt ذخیره می‌شود و قابل بازیابی نیست."""
        from app.core.security import hash_password, verify_password

        hashed = hash_password("my-secret")
        assert hashed != "my-secret"
        assert hashed.startswith("$2")  # قالب bcrypt
        assert verify_password("my-secret", hashed)
        assert not verify_password("wrong", hashed)


class TestLogin:
    """تست واحد ورود (AT-03)."""

    def test_login_success_returns_token_and_me(self, client):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "secret123"})
        assert r.status_code == 200
        token = r.json()["data"]["access_token"]
        assert token
        assert r.json()["data"]["user"]["username"] == uname
        # توکن معتبر برای /auth/me
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["data"]["username"] == uname

    def test_login_wrong_password_persian_401(self, client):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "wrong-pass"})
        assert r.status_code == 401
        message = r.json()["error"]["message"]
        assert "اشتباه" in message
        assert any("\u0600" <= ch <= "\u06FF" for ch in message)

    def test_login_unknown_user_same_error(self, client):
        """کاربر ناموجود — همان پیام (ضد user enumeration)."""
        r1 = client.post("/api/v1/auth/login", json={
            "username": f"nouser_{uuid.uuid4().hex[:6]}", "password": "whatever1"})
        assert r1.status_code == 401
        assert r1.json()["error"]["message"] == "نام کاربری یا رمز عبور اشتباه است."

    def test_login_updates_last_login(self, client):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "secret123"})
        assert r.json()["data"]["user"]["last_login_at"] is not None

    def test_protected_endpoint_without_token_401_persian(self, client):
        r = client.get("/api/v1/students/me")
        assert r.status_code == 401
        assert any("\u0600" <= ch <= "\u06FF" for ch in r.json()["error"]["message"])

    def test_invalid_token_401(self, client):
        r = client.get("/api/v1/auth/me",
                       headers={"Authorization": "Bearer not-a-real-token"})
        assert r.status_code == 401


class TestLogout:
    """Session Management — خروج، نشست را واقعاً لغو می‌کند."""

    def test_logout_revokes_session(self, client):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "secret123"})
        token = r.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # قبل از خروج کار می‌کند
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 200
        # خروج
        r = client.post("/api/v1/auth/logout", headers=headers)
        assert r.status_code == 200
        # بعد از خروج همان توکن پذیرفته نمی‌شود
        r = client.get("/api/v1/auth/me", headers=headers)
        assert r.status_code == 401
        assert "خاتمه" in r.json()["error"]["message"] or "منقضی" in r.json()["error"]["message"]


class TestPermission:
    """Permission Module — نقش‌های student و admin."""

    def test_first_user_is_admin_rest_are_students(self, tmp_path):
        """نخستین کاربر هر پایگاه داده تازه = مدیر (سند 01 §1.5)."""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from app.db.session import Base
        from app.modules import models_registry  # noqa: F401 — ثبت مدل‌ها
        from app.modules.identity.schemas import RegisterIn
        from app.modules.identity.service import create_user

        engine = create_engine(
            f"sqlite:///{tmp_path}/perm.db", connect_args={"check_same_thread": False})
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()

        first = create_user(db, RegisterIn(username="first_admin", password="secret123"))
        second = create_user(db, RegisterIn(username="second_student", password="secret123"))
        third = create_user(db, RegisterIn(username="third_student", password="secret123"))

        assert first.role == "admin"
        assert second.role == "student"
        assert third.role == "student"

    def test_require_admin_rejects_student(self):
        from app.modules.identity.models import User
        from app.modules.identity.service import require_admin
        from app.shared.exceptions import ForbiddenError

        student = User(username="s", password_hash="x", role="student")
        with pytest.raises(ForbiddenError) as exc:
            require_admin(user=student)
        assert "مدیر" in str(exc.value)

    def test_require_admin_allows_admin(self):
        from app.modules.identity.models import User
        from app.modules.identity.service import require_admin

        admin = User(username="a", password_hash="x", role="admin")
        assert require_admin(user=admin) is admin


# ---------- ابزار کمکی برای تست‌های نیازمند کاربر با full_name ----------

@pytest.fixture()
def auth_client_factory(client):
    """ثبت‌نام + ورود + برگرداندن کلاینت احراز هویت‌شده و نام کاربری."""
    def _make(full_name: str | None = None):
        uname = _uname()
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123", "full_name": full_name})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "secret123"})
        token = r.json()["data"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client, uname
    return _make
