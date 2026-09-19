"""تست رگرسیون تنظیمات — به‌روزرسانی دوبارهٔ یک سیاست باید اثر کند.

باگ قبلی: set_setting دیکشنری JSON را درجا mutate می‌کرد و SQLAlchemy
تغییر را تشخیص نمی‌داد؛ PUT دوم به بعد عملاً بی‌اثر بود.
"""
from __future__ import annotations

import uuid


def _client(client) -> object:
    uname = f"st_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/auth/register", json={"username": uname, "password": "secret123"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": "secret123"})
    client.headers.update({"Authorization": f"Bearer {r.json()['data']['access_token']}"})
    return client


def test_settings_update_persists_on_second_put(client):
    c = _client(client)
    c.put("/api/v1/settings", json={"exam_policy": {"max_questions": 5}})
    assert c.get("/api/v1/settings").json()["data"]["exam_policy"]["max_questions"] == 5

    c.put("/api/v1/settings", json={"exam_policy": {"max_questions": 120}})
    assert c.get("/api/v1/settings").json()["data"]["exam_policy"]["max_questions"] == 120


def test_settings_merge_keeps_other_keys(client):
    c = _client(client)
    c.put("/api/v1/settings", json={"scoring_policy": {"wrong_penalty": 0.25}})
    c.put("/api/v1/settings", json={"scoring_policy": {"wrong_penalty": 0.5}})
    # هر دو مقدار باید حفظ شوند — ادغام نه بازنویسی
    data = c.get("/api/v1/settings").json()["data"]["scoring_policy"]
    assert data["wrong_penalty"] == 0.5
    assert "review_policy" in c.get("/api/v1/settings").json()["data"]
