"""تست‌های API برنامه‌ریزی — اهداف، بلوک‌های زمانی، تولید هفتگی و ویرایش دستی.

سند 08 §8.4: بلوک‌های مدرسه/کلاس اشغال هستند؛ کاربر همیشه می‌تواند برنامه
تولیدشده را دستی ویرایش کند؛ برنامه روزانه می‌تواند خالی باشد.
"""
from __future__ import annotations

import copy
import datetime as dt
import uuid

import pytest

# شنبهٔ هفته جاری (jalali_weekday 0 = شنبه)
TODAY = dt.date.today()
WEEK_START = TODAY - dt.timedelta(days=(TODAY.weekday() + 2) % 7)  # شنبه (جلالی)


def _uname() -> str:
    return f"pl_{uuid.uuid4().hex[:8]}"


@pytest.fixture()
def planning_client(client):
    uname = _uname()
    client.post("/api/v1/auth/register", json={"username": uname, "password": "secret123"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": "secret123"})
    client.headers.update({"Authorization": f"Bearer {r.json()['data']['access_token']}"})
    return client


def _weekly_goal(client, **overrides) -> dict:
    start = WEEK_START
    payload = {
        "type": "weekly",
        "title": "۲۰ تست ریاضی",
        "target_value": {"minutes": 300, "subject": "ریاضی"},
        "start_date": start.isoformat(),
        "end_date": (start + dt.timedelta(days=6)).isoformat(),
        "status": "active",
    }
    payload.update(overrides)
    r = client.post("/api/v1/goals", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _blocks(client, blocks: list[dict]) -> dict:
    r = client.put("/api/v1/time-blocks", json={"blocks": blocks})
    assert r.status_code == 200, r.text
    return r.json()["data"]


class TestGoals:
    """مدیریت اهداف — بلندمدت/ماهانه/هفتگی."""

    def test_crud_all_three_types(self, planning_client):
        c = planning_client
        for gtype, label in [("long", "بلندمدت"), ("monthly", "ماهانه"), ("weekly", "هفتگی")]:
            g = _weekly_goal(c, type=gtype, title=f"هدف {label}")
            assert g["type"] == gtype
            assert g["type_label"] == label

        r = c.get("/api/v1/goals")
        types = {g["type"] for g in r.json()["data"]}
        assert types == {"long", "monthly", "weekly"}

    def test_filter_by_type(self, planning_client):
        c = planning_client
        _weekly_goal(c, type="long")
        _weekly_goal(c, type="weekly")
        r = c.get("/api/v1/goals", params={"type": "weekly"})
        assert {g["type"] for g in r.json()["data"]} == {"weekly"}

    def test_update_and_delete(self, planning_client):
        c = planning_client
        g = _weekly_goal(c)
        r = c.put(f"/api/v1/goals/{g['id']}",
                  json={"title": "عنوان جدید", "status": "completed"})
        assert r.json()["data"]["title"] == "عنوان جدید"
        assert r.json()["data"]["status"] == "completed"
        assert c.delete(f"/api/v1/goals/{g['id']}").status_code == 200
        assert c.get("/api/v1/goals").json()["data"] == []

    def test_invalid_type_rejected(self, planning_client):
        r = planning_client.post("/api/v1/goals", json={
            "type": "yearly", "title": "نامعتبر",
            "start_date": WEEK_START.isoformat(),
            "end_date": (WEEK_START + dt.timedelta(days=6)).isoformat(),
        })
        assert r.status_code == 422


class TestTimeBlocks:
    """بلوک‌های زمانی — مدرسه/کلاس/مطالعه/آزاد."""

    ALL_TYPES = [
        {"day_of_week": 0, "start_time": "07:30", "end_time": "13:30", "block_type": "school", "title": "مدرسه"},
        {"day_of_week": 1, "start_time": "16:00", "end_time": "18:00", "block_type": "class", "title": "کلاس کنکور"},
        {"day_of_week": 2, "start_time": "20:00", "end_time": "21:30", "block_type": "study", "title": "مرور ثابت"},
        {"day_of_week": 4, "start_time": "22:00", "end_time": "23:00", "block_type": "free", "title": "استراحت"},
    ]

    def test_replace_all_four_types(self, planning_client):
        data = _blocks(planning_client, self.ALL_TYPES)
        assert len(data) == 4
        types = {b["block_type"] for b in data}
        assert types == {"school", "class", "study", "free"}
        # جایگزینی کامل
        _blocks(planning_client, self.ALL_TYPES[:1])
        assert len(planning_client.get("/api/v1/time-blocks").json()["data"]) == 1

    def test_invalid_block_type_rejected(self, planning_client):
        r = planning_client.put("/api/v1/time-blocks", json={"blocks": [
            {"day_of_week": 0, "start_time": "07:00", "end_time": "08:00", "block_type": "gym"},
        ]})
        assert r.status_code == 422

    def test_end_before_start_rejected(self, planning_client):
        r = planning_client.put("/api/v1/time-blocks", json={"blocks": [
            {"day_of_week": 0, "start_time": "14:00", "end_time": "08:00", "block_type": "school"},
        ]})
        assert r.status_code == 422
        assert "بعد از ساعت شروع" in r.text


class TestGenerateWeek:
    """تولید برنامه هفتگی (AT-17) — بلوک‌های اشغال + اهداف."""

    def test_requires_saturday_start(self, planning_client):
        r = planning_client.post("/api/v1/plans/generate-week",
                                 json={"week_start": (WEEK_START + dt.timedelta(days=1)).isoformat()})
        assert r.status_code == 422
        assert "شنبه" in r.json()["error"]["message"]

    def test_occupied_blocks_excluded_from_plan(self, planning_client):
        c = planning_client
        _blocks(c, [{"day_of_week": 0, "start_time": "07:00", "end_time": "14:00",
                     "block_type": "school"}])
        _weekly_goal(c)
        data = c.post("/api/v1/plans/generate-week",
                      json={"week_start": WEEK_START.isoformat()}).json()["data"]
        assert data["week_start"] == WEEK_START.isoformat()
        assert len(data["plans"]) == 7

        day0 = data["plans"][0]  # شنبه
        for item in day0["items"]:
            overlap = item["start"] < "14:00" and item["end"] > "07:00"
            assert not overlap, f"آیتم {item['start']}–{item['end']} با مدرسه 07:00–14:00 تداخل دارد"

    def test_goal_minutes_distributed(self, planning_client):
        c = planning_client
        _weekly_goal(c)  # 300 دقیقه در هفته
        data = c.post("/api/v1/plans/generate-week",
                      json={"week_start": WEEK_START.isoformat()}).json()["data"]
        total = sum(p["summary"]["total_minutes"] for p in data["plans"])
        assert total >= 300, "کل دقیقه‌های برنامه باید دست‌کم سهم اهداف هفتگی را پوشش دهد"

    def test_empty_week_without_goals_or_blocks(self, planning_client):
        """برنامه روزانه می‌تواند خالی باشد (سند 08 §8.4)."""
        data = planning_client.post("/api/v1/plans/generate-week",
                                    json={"week_start": WEEK_START.isoformat()}).json()["data"]
        assert all(p["items"] == [] for p in data["plans"])


class TestManualPlanEdit:
    """ویرایش دستی برنامه (AT-18) — کاربر همیشه می‌تواند تغییر دهد."""

    def test_manual_edit_persists(self, planning_client):
        c = planning_client
        day = WEEK_START + dt.timedelta(days=2)  # دوشنبه
        items = [{"start": "15:00", "end": "16:30", "title": "هندسه — فصل دایره",
                  "subject": "هندسه", "type": "study", "done": False}]
        r = c.put(f"/api/v1/plans/{day.isoformat()}", json={"items": items})
        assert r.status_code == 200
        saved = r.json()["data"]
        assert saved["items"][0]["title"] == "هندسه — فصل دایره"
        assert saved["summary"]["total_minutes"] == 90

        # خواندن مجدد
        again = c.get("/api/v1/plans", params={"date": day.isoformat()}).json()["data"]
        assert again["items"][0]["title"] == "هندسه — فصل دایره"

    def test_manual_edit_overrides_generation(self, planning_client):
        c = planning_client
        _weekly_goal(c)
        c.post("/api/v1/plans/generate-week",
               json={"week_start": WEEK_START.isoformat()})
        day = WEEK_START
        custom = [{"start": "21:00", "end": "21:45", "title": "مرور دستی من",
                   "type": "study", "done": True}]
        c.put(f"/api/v1/plans/{day.isoformat()}", json={"items": custom})
        saved = c.get("/api/v1/plans", params={"date": day.isoformat()}).json()["data"]
        assert [i["title"] for i in saved["items"]] == ["مرور دستی من"]
        assert saved["items"][0]["done"] is True

    def test_item_end_before_start_rejected(self, planning_client):
        day = WEEK_START
        r = planning_client.put(f"/api/v1/plans/{day.isoformat()}", json={
            "items": [{"start": "18:00", "end": "17:00", "title": "نامعتبر"}]})
        assert r.status_code == 422
        assert "بعد از ساعت شروع" in r.text

    def test_empty_day_allowed(self, planning_client):
        day = WEEK_START + dt.timedelta(days=6)
        r = planning_client.put(f"/api/v1/plans/{day.isoformat()}",
                                json={"items": []})
        assert r.status_code == 200
        assert r.json()["data"]["items"] == []
