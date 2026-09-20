"""Phase 1 — register/login/logout/me + JWT (doc 06 §Auth)."""
from __future__ import annotations

EMAIL = "sara@example.com"
PASS = "pass1234"


def _register(client, email=EMAIL, password=PASS, name="سارا"):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": name},
    )


def test_register_returns_token_and_profile(client):
    r = _register(client)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == EMAIL
    assert data["user"]["role"] == "student"
    assert data["student"] is not None
    assert data["student"]["grade"] is None


def test_me_with_token(client):
    token = _register(client, email="ali@example.com").json()["data"]["access_token"]
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["user"]["email"] == "ali@example.com"


def test_me_without_token_401_persian(client):
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 401
    body = r.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert body["error"]["message"]


def test_login_ok_and_wrong_password(client):
    _register(client, email="login@example.com")
    ok_r = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": PASS})
    assert ok_r.status_code == 200
    assert ok_r.json()["data"]["access_token"]

    bad_r = client.post("/api/v1/auth/login", json={"email": "login@example.com", "password": "wrong-pass"})
    assert bad_r.status_code == 401
    assert bad_r.json()["error"]["message"] == "ایمیل یا رمز عبور نادرست است."


def test_register_duplicate_email_409_persian(client):
    _register(client, email="dup@example.com")
    r = client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": PASS})
    assert r.status_code == 409
    assert r.json()["error"]["message"] == "این ایمیل قبلاً ثبت شده است."


def test_register_short_password_422(client):
    r = client.post("/api/v1/auth/register", json={"email": "short@example.com", "password": "123"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"
    assert r.json()["error"]["message"] == "ورودی‌ها درست نیستند."


def test_logout(client):
    token = _register(client, email="logout@example.com").json()["data"]["access_token"]
    r = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["data"]["logged_out"] is True


def test_tampered_token_rejected(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert r.status_code == 401
