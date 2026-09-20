"""Phase 4 — Settings (doc 06 GET/PUT /settings, doc 08 §8.1/§8.4, doc 10 §10.2-10.3)."""
from __future__ import annotations

PASS = "pass1234"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


def test_settings_defaults(client):
    u = _user(client, "set1@example.com")
    r = client.get("/api/v1/settings", headers=_h(u))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["review_intervals"] == [1, 3, 7, 14]  # doc 10 §10.2
    assert data["max_daily_review"] == 25             # doc 10 §10.3
    assert data["min_cluster"] == 8                   # doc 10 §10.3
    assert data["include_blank_in_review"] is False   # doc 08 §8.4
    assert data["konkurs_penalty_k"] == 0.33          # doc 08 §8.1


def test_settings_put_roundtrip(client):
    u = _user(client, "set2@example.com")
    r = client.put(
        "/api/v1/settings",
        json={"review_intervals": [1, 2, 4], "max_daily_review": 10, "include_blank_in_review": True},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["review_intervals"] == [1, 2, 4]
    assert data["max_daily_review"] == 10
    assert data["include_blank_in_review"] is True
    # بقیه دست‌نخورده
    assert data["min_cluster"] == 8

    g = client.get("/api/v1/settings", headers=_h(u)).json()["data"]
    assert g["review_intervals"] == [1, 2, 4]

    # برگرداندن به پیش‌فرض (پاکسازی برای بقیه تست‌ها)
    client.put(
        "/api/v1/settings",
        json={"review_intervals": [1, 3, 7, 14], "max_daily_review": 25, "include_blank_in_review": False},
        headers=_h(u),
    )


def test_settings_validation_persian(client):
    u = _user(client, "set3@example.com")
    r = client.put("/api/v1/settings", json={"review_intervals": []}, headers=_h(u))
    assert r.status_code == 422
    assert "چرخه مرور" in r.json()["error"]["message"]

    r2 = client.put("/api/v1/settings", json={"max_daily_review": 0}, headers=_h(u))
    assert r2.status_code == 422
    assert "سقف مرور روزانه" in r2.json()["error"]["message"]

    r3 = client.put("/api/v1/settings", json={"konkurs_penalty_k": 2}, headers=_h(u))
    assert r3.status_code == 422
    assert "ضریب جریمه" in r3.json()["error"]["message"]


def test_settings_require_auth(client):
    r = client.get("/api/v1/settings")
    assert r.status_code == 401
    assert r.json()["error"]["message"] == "برای ادامه باید وارد شوید."
