"""فاز ۷ — Rewards & Behavior (doc 13، doc 08 §8.9-8.10).

points ledger append-only + idempotent · streak شمسی با reset و grace · badges seed (OD4) ·
habit advice فقط با data_days>=30 · procrastination aid · recommendation با explain_fa فارسی.
"""
from __future__ import annotations

import datetime as dt

from tests.test_planning import _h, _user
from tests.test_exam_analytics import _session, _setup

from app.core.jalali import gregorian_to_jalali
from app.modules.rewards import domain
from app.modules.rewards.models import PointsEntry

TZ_TEHRAN = dt.timezone(dt.timedelta(hours=3, minutes=30))
DIMS = {"energy": 3, "focus": 4, "motivation": 3, "stress": 2, "fatigue": 2}


def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).astimezone(TZ_TEHRAN).date()


def _jiso(d: dt.date) -> str:
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def _summary(client, u):
    r = client.get("/api/v1/rewards/summary", headers=_h(u))
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _award_days(db, student_id: str, days: list[tuple[dt.date, str, int]]):
    """روزهای ledger را مستقیم می‌سازد — (gregorian date, source, n entries)."""
    for i, (d, src, n) in enumerate(days):
        for j in range(n):
            db.add(PointsEntry(
                student_id=student_id, source_event=src, ref_id=f"seed-{i}-{j}",
                points=domain.POINTS_BY_SOURCE[src], active_date=_jiso(d),
                created_at=dt.datetime.now(dt.timezone.utc),
            ))
    db.commit()


def _student_id(client, u) -> str:
    r = client.get("/api/v1/students/me", headers=_h(u))
    return r.json()["data"]["id"]


# --- domain (pure) --------------------------------------------------------------------------

def test_domain_streaks_current_longest_reset():
    t = _today()
    assert domain.streaks_from_days([], t) == (0, 0)
    assert domain.streaks_from_days([t, t - dt.timedelta(days=1), t - dt.timedelta(days=2)], t) == (3, 3)
    # دیروز فعال، امروز هنوز نه → streak زنده است (روز جاری تمام نشده)
    assert domain.streaks_from_days([t - dt.timedelta(days=1), t - dt.timedelta(days=2)], t) == (2, 2)
    # روز از دست رفته → reset (grace=0)
    old = [t - dt.timedelta(days=3), t - dt.timedelta(days=4)]
    assert domain.streaks_from_days(old, t) == (0, 2)
    # grace=1 → فقط «یک» روز پریده قابل بخشش است (آخرین فعالیت دیروزِ پریده)
    one_missed = [t - dt.timedelta(days=2), t - dt.timedelta(days=3)]
    assert domain.streaks_from_days(one_missed, t) == (0, 2)
    assert domain.streaks_from_days(one_missed, t, grace=1) == (2, 2)
    # longest بدون grace — شکست میانی longest را نمی‌شکند
    mixed = [t, t - dt.timedelta(days=1), t - dt.timedelta(days=3), t - dt.timedelta(days=4), t - dt.timedelta(days=5)]
    assert domain.streaks_from_days(mixed, t) == (2, 3)


def test_domain_habit_advice_gate_and_median():
    assert domain.habit_advice([2, 3], 29) is None           # data_days < 30 → هرگز
    assert domain.habit_advice([], 40) is None               # روزی با انجام واقعی نیست
    adv = domain.habit_advice([1, 2, 2, 3, 100], 31)         # میانه ۲
    assert adv is not None and adv["suggested_daily_tasks"] == 2
    assert adv["data_days"] == 31 and adv["message_fa"]


def test_domain_procrastination_aid_rules():
    # completion خوب → هیچ کمکی لازم نیست
    assert domain.procrastination_aid(
        [{"done": 2, "total": 2}, {"done": 1, "total": 2}], [], None) is None
    # فقط یک روز با task → کافی نیست
    assert domain.procrastination_aid([{"done": 0, "total": 3}], [{"id": "t", "title": "x", "minutes": 90}], None) is None
    # rate پایین + task بزرگ باز → split
    aid = domain.procrastination_aid(
        [{"done": 0, "total": 2}, {"done": 1, "total": 4}], [{"id": "t1", "title": "فیزیک جامع", "minutes": 90}], None)
    assert aid is not None and aid["kind"] == "split" and aid["task_id"] == "t1" and "تقسیم" in aid["message_fa"]
    # rate پایین بدون task بزرگ ولی با مبحث ضعیف → شروع نرم با ۵ تست آسان
    aid2 = domain.procrastination_aid(
        [{"done": 0, "total": 2}, {"done": 0, "total": 2}], [], {"topic_id": "x", "topic_title": "تابع"})
    assert aid2 is not None and aid2["kind"] == "easy_start" and "۵ تست آسان" in aid2["message_fa"]


# --- points & streak (live API) ---------------------------------------------------------------

def test_points_session_streak_and_badges(client):
    u, rid, _topic = _setup(client, "rw1@example.com")
    _session(client, u, rid, correct=(1, 2), wrong=(3,))
    s = _summary(client, u)
    assert s["points_total"] == domain.POINTS_BY_SOURCE[domain.SOURCE_SESSION]  # ۱۰
    assert s["streak"]["current"] == 1 and s["streak"]["longest"] == 1
    assert s["streak"]["last_active_date"] == _jiso(_today())
    assert s["points_by_source"][domain.SOURCE_FA[domain.SOURCE_SESSION]] == 1
    assert s["badges"]["earned_count"] >= 1  # قدم اول
    b = client.get("/api/v1/rewards/badges", headers=_h(u)).json()["data"]
    codes = {i["code"]: i for i in b["items"]}
    assert codes["first_step"]["earned"] is True and codes["first_step"]["awarded_at"]
    assert codes["streak_30"]["earned"] is False
    assert codes["streak_30"]["progress"]["target"] == 30


def test_points_all_four_sources(client):
    u, rid, topic = _setup(client, "rw2@example.com", taught=True)
    _session(client, u, rid, correct=(1,), wrong=(2, 3))     # session ۱۰ + review queue
    client.post("/api/v1/students/me/checkin", json=DIMS, headers=_h(u))          # ۳
    day = client.put(f"/api/v1/plans/{_today().isoformat()}", headers=_h(u),
                     json={"tasks": [{"title": "مطالعه تابع", "minutes": 30}]}).json()["data"]
    client.post(f"/api/v1/plans/tasks/{day['tasks'][0]['id']}/status", headers=_h(u), json={"status": "done"})  # ۵
    q = client.get("/api/v1/reviews/queue", headers=_h(u)).json()["data"]
    assert q["due_count"] >= 1
    client.post(f"/api/v1/reviews/{q['items'][0]['id']}/complete", headers=_h(u))  # ۲
    s = _summary(client, u)
    assert s["points_total"] == 10 + 3 + 5 + 2
    by = s["points_by_source"]
    assert by[domain.SOURCE_FA[domain.SOURCE_TASK]] == 1
    assert by[domain.SOURCE_FA[domain.SOURCE_REVIEW]] == 1
    assert by[domain.SOURCE_FA[domain.SOURCE_SESSION]] == 1
    assert by[domain.SOURCE_FA[domain.SOURCE_CHECKIN]] == 1
    # 13.6 — state از check-in
    lc = s["latest_checkin"]
    assert lc["energy"] == 3 and lc["date_jalali"] == _jiso(_today())


def test_points_idempotent_no_double_award(client):
    u, rid, _topic = _setup(client, "rw3@example.com")
    sess = _session(client, u, rid, correct=(1,))
    client.post(f"/api/v1/test-sessions/{sess['id']}/finish", json={}, headers=_h(u))  # finish ایدمپوتنت
    client.post("/api/v1/students/me/checkin", json=DIMS, headers=_h(u))
    client.post("/api/v1/students/me/checkin", json={**DIMS, "energy": 5}, headers=_h(u))  # upsert روز
    day = client.put(f"/api/v1/plans/{_today().isoformat()}", headers=_h(u),
                     json={"tasks": [{"title": "کار", "minutes": 20}]}).json()["data"]
    tid = day["tasks"][0]["id"]
    client.post(f"/api/v1/plans/tasks/{tid}/status", headers=_h(u), json={"status": "done"})
    client.post(f"/api/v1/plans/tasks/{tid}/status", headers=_h(u), json={"status": "pending"})
    client.post(f"/api/v1/plans/tasks/{tid}/status", headers=_h(u), json={"status": "done"})
    s = _summary(client, u)
    # ledger append-only — هر رویداد یک بار: ۱۰ + ۳ + ۵
    assert s["points_total"] == 18


def test_streak_from_ledger_days_and_reset(client, db):
    u = _user(client, "rw4@example.com")
    sid = _student_id(client, u)
    t = _today()
    _award_days(db, sid, [(t, domain.SOURCE_CHECKIN, 1),
                          (t - dt.timedelta(days=1), domain.SOURCE_CHECKIN, 1),
                          (t - dt.timedelta(days=2), domain.SOURCE_CHECKIN, 1)])
    s = _summary(client, u)
    assert s["streak"]["current"] == 3 and s["streak"]["longest"] == 3

    u2 = _user(client, "rw5@example.com")
    sid2 = _student_id(client, u2)
    _award_days(db, sid2, [(t - dt.timedelta(days=4), domain.SOURCE_CHECKIN, 1),
                           (t - dt.timedelta(days=5), domain.SOURCE_CHECKIN, 1)])
    s2 = _summary(client, u2)
    assert s2["streak"]["current"] == 0 and s2["streak"]["longest"] == 2  # روز از دست رفته → reset


def test_streak_grace_setting(client, db):
    u = _user(client, "rw6@example.com")
    sid = _student_id(client, u)
    t = _today()
    _award_days(db, sid, [(t - dt.timedelta(days=2), domain.SOURCE_CHECKIN, 1),
                          (t - dt.timedelta(days=3), domain.SOURCE_CHECKIN, 1)])
    assert _summary(client, u)["streak"]["current"] == 0     # grace=0 پیش‌فرض
    r = client.put("/api/v1/settings", json={"streak_grace_days": 1}, headers=_h(u))
    assert r.status_code == 200, r.text
    assert r.json()["data"]["streak_grace_days"] == 1
    assert _summary(client, u)["streak"]["current"] == 2     # یک روز پریده بخشیده شد
    bad = client.put("/api/v1/settings", json={"streak_grace_days": 99}, headers=_h(u))
    assert bad.status_code == 422 and "ارفاق" in bad.json()["error"]["message"]
    client.put("/api/v1/settings", json={"streak_grace_days": 0}, headers=_h(u))  # بازگردانی (db مشترک)
    assert _summary(client, u)["streak"]["current"] == 0


def test_badges_seed_size_od4(client):
    u = _user(client, "rw7@example.com")
    b = client.get("/api/v1/rewards/badges", headers=_h(u)).json()["data"]
    assert 8 <= len(b["items"]) <= 12                        # OD4: ۸ تا ۱۲
    for it in b["items"]:
        assert it["code"] and it["title_fa"] and it["target"] > 0
        assert it["earned"] is False and it["awarded_at"] is None
    assert b["earned_count"] == 0


def test_badge_award_unique_per_user(client, db):
    u, rid, _t = _setup(client, "rw8@example.com")
    _session(client, u, rid, correct=(1,))
    _session(client, u, rid, correct=(2,))
    b = client.get("/api/v1/rewards/badges", headers=_h(u)).json()["data"]
    fs = [i for i in b["items"] if i["code"] == "first_step"][0]
    assert fs["earned"] is True
    assert b["earned_count"] == len([i for i in b["items"] if i["earned"]])
    # امضای یکتا: حتی با چند فعالیت، awarded_at یکی می‌ماند
    assert fs["awarded_at"]


# --- habit advice (13.4) ---------------------------------------------------------------------

def test_habit_advice_hidden_below_30_days(client):
    u, rid, _t = _setup(client, "rw9@example.com")
    _session(client, u, rid, correct=(1,))
    s = _summary(client, u)
    assert s["habit_advice"]["available"] is False
    assert s["habit_advice"]["data_days"] < 30
    assert "suggested_daily_tasks" not in s["habit_advice"]   # doc 08 §8.9 — نمایش داده نشود


def test_habit_advice_after_30_data_days(client, db):
    u = _user(client, "rw10@example.com")
    sid = _student_id(client, u)
    t = _today()
    days = [(t - dt.timedelta(days=i), domain.SOURCE_TASK, 2) for i in range(1, 32)]  # ۳۱ روز × ۲ کار
    _award_days(db, sid, days)
    s = _summary(client, u)
    ha = s["habit_advice"]
    assert ha["available"] is True and ha["data_days"] == 31
    assert ha["suggested_daily_tasks"] == 2                   # میانه انجام واقعی
    assert "واقع‌بینانه" in ha["message_fa"]


# --- procrastination aid (13.5) ---------------------------------------------------------------

def test_procrastination_split_and_recommendation(client):
    u, rid, topic = _setup(client, "rw11@example.com")
    t = _today()
    y = (t - dt.timedelta(days=1)).isoformat()
    client.put(f"/api/v1/plans/{y}", headers=_h(u), json={"tasks": [{"title": "کار دیروز", "minutes": 30}]})
    today_plan = client.put(f"/api/v1/plans/{t.isoformat()}", headers=_h(u),
                            json={"tasks": [{"title": "فیزیک جامع", "minutes": 90}]}).json()["data"]
    big_id = today_plan["tasks"][0]["id"]
    s = _summary(client, u)
    aid = s["procrastination"]
    assert aid is not None and aid["kind"] == "split" and aid["task_id"] == big_id
    assert aid["avg_completion_rate"] < 0.5 and "تقسیم" in aid["message_fa"]
    # recommendation امروز همان split است + explain فارسی (doc 07 §7.6 #6)
    today = client.get("/api/v1/today", headers=_h(u)).json()["data"]
    rec = today["recommendation"]
    assert rec is not None
    assert "procrastination_split" in [r["code"] for r in rec["reasons"]]
    assert rec["reasons"][0]["fa"]                            # §8.10 — دلیل فارسی
    assert "تقسیم" in rec["payload"]["title"]
    assert rec["payload"]["explain_fa"] and "کمتر از نصف" in rec["payload"]["explain_fa"]


def test_procrastination_easy_start_rec(client, db):
    from app.modules.review.models import LearningState
    u, rid, topic = _setup(client, "rw12@example.com")
    t = _today()
    for i in (1, 2):
        d = (t - dt.timedelta(days=i)).isoformat()
        client.put(f"/api/v1/plans/{d}", headers=_h(u), json={"tasks": [{"title": f"کار {i}", "minutes": 20}]})
    # امروز هیچ کاری نیست → rec از aid می‌آید
    db.add(LearningState(student_id=_student_id(client, u), topic_id=topic, coverage=0.5,
                         accuracy=0.2, exam_readiness=0.2, confidence=0.3, weakness=True))
    db.commit()
    s = _summary(client, u)
    aid = s["procrastination"]
    assert aid is not None and aid["kind"] == "easy_start" and aid["topic_title"] == "تابع"
    today = client.get("/api/v1/today", headers=_h(u)).json()["data"]
    rec = today["recommendation"]
    assert rec["payload"]["kind"] == "test_easy" and "۵ تست آسان" in rec["payload"]["title"]
    assert "procrastination_start" in [r["code"] for r in rec["reasons"]]
    assert rec["payload"]["explain_fa"]


def test_recommendation_explain_fa_always_present(client):
    u = _user(client, "rw13@example.com")
    today = client.get("/api/v1/today", headers=_h(u)).json()["data"]
    rec = today["recommendation"]
    assert rec is not None
    assert rec["payload"]["explain_fa"]                       # حتی برای no_demand
    assert rec["reasons"] and all(r["fa"] for r in rec["reasons"])


# --- endpoint hygiene -------------------------------------------------------------------------

def test_rewards_unauth_and_settings_key(client):
    assert client.get("/api/v1/rewards/summary").status_code == 401
    assert client.get("/api/v1/rewards/badges").status_code == 401
    u = _user(client, "rw14@example.com")
    st = client.get("/api/v1/settings", headers=_h(u)).json()["data"]
    assert st["streak_grace_days"] == 0                       # doc 13.2 — پیش‌فرض grace=0
