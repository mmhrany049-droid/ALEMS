"""تست جریان کامل فاز ۱ — ثبت‌نام → ورود → تکمیل پروفایل → ثبت انرژی روزانه.

این تست دقیقاً مسیر اصلی کاربر جدید را گام‌به‌گام شبیه‌سازی می‌کند
(معادل همان مسیری که در UI طی می‌شود: AuthPage → OnboardingPage → Today Hub).
"""
from __future__ import annotations

import datetime as dt
import uuid


def test_phase1_complete_flow(client):
    """مسیر کامل: ثبت‌نام → ورود → پروفایل ناقص → تکمیل → وضعیت روزانه → upsert."""
    uname = f"flow_{uuid.uuid4().hex[:8]}"
    H = {}

    # ---------- گام ۱: ثبت‌نام ----------
    r = client.post("/api/v1/auth/register", json={
        "username": uname, "password": "secret123", "full_name": "دانش‌آموز جریان"})
    assert r.status_code == 200, r.text
    user = r.json()["data"]
    assert user["username"] == uname
    assert "password_hash" not in user

    # ---------- گام ۲: ورود و دریافت توکن ----------
    r = client.post("/api/v1/auth/login", json={
        "username": uname, "password": "secret123"})
    assert r.status_code == 200
    token = r.json()["data"]["access_token"]
    H = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/v1/auth/me", headers=H)
    assert r.status_code == 200
    assert r.json()["data"]["username"] == uname

    # ---------- گام ۳: پروفایل ناقص است (سند 8.6 → UI به آغازکار هدایت می‌کند) ----------
    r = client.get("/api/v1/students/me", headers=H)
    assert r.status_code == 200
    profile = r.json()["data"]
    assert profile["is_complete"] is False
    assert profile["full_name"] == "دانش‌آموز جریان"  # از ثبت‌نام آمده

    # ---------- گام ۴: تکمیل پروفایل (AT-04) ----------
    r = client.put("/api/v1/students/me", headers=H, json={
        "full_name": "دانش‌آموز جریان",
        "grade": "دوازدهم",
        "field": "تجربی",
        "academic_year": "1404-1405",
        "target_rank": 750,
        "target_major": "پزشکی",
    })
    assert r.status_code == 200, r.text
    profile = r.json()["data"]
    assert profile["is_complete"] is True
    assert profile["grade"] == "دوازدهم"
    assert profile["field"] == "تجربی"
    assert profile["target_rank"] == 750
    assert profile["target_major"] == "پزشکی"
    profile_id = profile["id"]

    # ---------- گام ۵: به‌روزرسانی هدف — همان رکورد، نه رکورد جدید ----------
    r = client.put("/api/v1/students/me", headers=H, json={
        "full_name": "دانش‌آموز جریان", "grade": "دوازدهم", "field": "تجربی",
        "target_rank": 500,
    })
    assert r.status_code == 200
    assert r.json()["data"]["id"] == profile_id  # upsert
    assert r.json()["data"]["target_rank"] == 500

    # ---------- گام ۶: ثبت وضعیت روزانه — انرژی و حال (AT-05) ----------
    today = dt.date.today().isoformat()
    r = client.post("/api/v1/students/me/state", headers=H, json={
        "date": today,
        "energy_level": 4,
        "mood": "خوب",
        "study_condition": "متمرکز",
        "note": "بعد از امتحان فیزیک",
    })
    assert r.status_code == 200, r.text
    state = r.json()["data"]
    assert state["energy_level"] == 4
    assert state["mood"] == "خوب"
    assert state["weekday"] in range(7)  # ۰=شنبه ... ۶=جمعه

    # ---------- گام ۷: ثبت مجدد همان روز = به‌روزرسانی (نه رکورد جدید) ----------
    r = client.post("/api/v1/students/me/state", headers=H, json={
        "date": today, "energy_level": 2, "mood": "خسته",
    })
    assert r.status_code == 200
    assert r.json()["data"]["id"] == state["id"]  # همان رکورد upsert شد
    assert r.json()["data"]["energy_level"] == 2

    # ---------- گام ۸: خواندن بازه — فیلتر inclusive ----------
    r = client.get(
        f"/api/v1/students/me/state?from={today}&to={today}", headers=H)
    assert r.status_code == 200
    states = r.json()["data"]
    assert len(states) == 1
    assert states[0]["energy_level"] == 2

    # ---------- گام ۹: خطاهای فارسی در طول مسیر ----------
    # انرژی خارج از ۱..۵
    r = client.post("/api/v1/students/me/state", headers=H, json={"energy_level": 9})
    assert r.status_code == 422
    assert any("\u0600" <= ch <= "\u06FF" for ch in r.json()["error"]["message"])
    # پایه نامعتبر
    r = client.put("/api/v1/students/me", headers=H, json={
        "full_name": "نام", "grade": "پنجم", "field": "تجربی"})
    assert r.status_code == 422
    # ورود با رمز اشتباه (AT-03)
    r = client.post("/api/v1/auth/login", json={
        "username": uname, "password": "not-the-pass"})
    assert r.status_code == 401
    assert any("\u0600" <= ch <= "\u06FF" for ch in r.json()["error"]["message"])

    # ---------- گام ۱۰: خروج — نشست لغو می‌شود ----------
    r = client.post("/api/v1/auth/logout", headers=H)
    assert r.status_code == 200
    r = client.get("/api/v1/auth/me", headers=H)
    assert r.status_code == 401


def test_two_profiles_on_same_device_are_isolated(client):
    """چندپروفایل روی یک دستگاه: داده هر کاربر فقط برای خودش دیده می‌شود."""
    users = []
    for i in range(2):
        uname = f"iso_{i}_{uuid.uuid4().hex[:6]}"
        client.post("/api/v1/auth/register", json={
            "username": uname, "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": uname, "password": "secret123"})
        token = r.json()["data"]["access_token"]
        users.append({"token": token, "uname": uname})

    # هر کاربر پروفایل و وضعیت خودش را ثبت می‌کند
    for i, u in enumerate(users):
        h = {"Authorization": f"Bearer {u['token']}"}
        r = client.put("/api/v1/students/me", headers=h, json={
            "full_name": f"کاربر {i}", "grade": "دهم", "field": "ریاضی"})
        assert r.status_code == 200
        r = client.post("/api/v1/students/me/state", headers=h, json={
            "energy_level": i + 1})
        assert r.status_code == 200

    # وضعیت‌ها قاطی نمی‌شوند
    for i, u in enumerate(users):
        h = {"Authorization": f"Bearer {u['token']}"}
        r = client.get("/api/v1/students/me/state", headers=h)
        rows = r.json()["data"]
        assert len(rows) == 1
        assert rows[0]["energy_level"] == i + 1
        r = client.get("/api/v1/students/me", headers=h)
        assert r.json()["data"]["full_name"] == f"کاربر {i}"
