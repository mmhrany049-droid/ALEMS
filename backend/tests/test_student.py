"""Phase 1 — profile, check-in upsert, state (doc 06 §Student, doc 13 §13.6)."""
from __future__ import annotations

PASS = "pass1234"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    return {"token": data["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


DIMS = {"energy": 3, "focus": 4, "motivation": 5, "stress": 2, "fatigue": 2}


def test_profile_put_get(client):
    u = _user(client, "prof1@example.com")
    r = client.put("/api/v1/students/me", json={"grade": "دوازدهم", "track": "علوم تجربی", "target": "پزشکی"}, headers=_h(u))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["grade"] == "دوازدهم"
    assert data["track"] == "علوم تجربی"
    assert data["target"] == "پزشکی"

    g = client.get("/api/v1/students/me", headers=_h(u))
    assert g.json()["data"]["track"] == "علوم تجربی"


def test_checkin_creates_state(client):
    u = _user(client, "ck1@example.com")
    r = client.post("/api/v1/students/me/checkin", json=DIMS, headers=_h(u))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["today"] is not None
    assert data["today"]["energy"] == 3
    assert data["today"]["date_jalali"].startswith("1405/")
    assert data["data_days"] == 1


def test_checkin_same_day_upserts_not_duplicate(client):
    u = _user(client, "ck2@example.com")
    client.post("/api/v1/students/me/checkin", json=DIMS, headers=_h(u))
    r = client.post("/api/v1/students/me/checkin", json={**DIMS, "energy": 5}, headers=_h(u))
    assert r.status_code == 200
    data = r.json()["data"]
    # upsert: same day, updated value, still one day of data
    assert data["today"]["energy"] == 5
    assert data["data_days"] == 1

    g = client.get("/api/v1/students/me/state", headers=_h(u))
    st = g.json()["data"]
    assert st["today"]["energy"] == 5
    assert st["data_days"] == 1
    assert st["last"]["date"] == st["today"]["date"]


def test_checkin_invalid_dimension_422_persian(client):
    u = _user(client, "ck3@example.com")
    r = client.post("/api/v1/students/me/checkin", json={**DIMS, "focus": 9}, headers=_h(u))
    # pydantic ge/le -> 422 envelope (Persian)
    assert r.status_code == 422
    assert r.json()["error"]["message"] == "ورودی‌ها درست نیستند."


def test_state_without_checkin(client):
    u = _user(client, "ck4@example.com")
    r = client.get("/api/v1/students/me/state", headers=_h(u))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["today"] is None
    assert data["last"] is None
    assert data["data_days"] == 0


def test_state_requires_auth(client):
    r = client.get("/api/v1/students/me/state")
    assert r.status_code == 401
