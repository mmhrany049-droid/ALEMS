"""Phase 5 — Planning & Capacity & Today (doc 11، doc 08 §8.6-8.7، doc 15 V2-P01..P04).

- time blocks مدرسه/کلاس/آزاد + school override (V2-P02)
- capacity = f(free, school, class, completion 7d, state وزن پایین)
- generate-week با pipeline ۱۲مرحله‌ای لاگ‌شده (doc 11.3)
- manual override: add/remove/move/split/merge/count/lock — locked بعد از regenerate می‌ماند (V2-P03)
- recovery بدون dump روی فردا (V2-P04)
- GET /today کامل (V2-P01) + recommendation با reason فارسی (doc 08 §8.10)
"""
from __future__ import annotations

import datetime as dt

from app.modules.planning import domain

PASS = "pass1234"
TODAY = dt.date(2026, 9, 20)          # یکشنبه ۱۴۰۵/۰۶/۲۹
SATURDAY = dt.date(2026, 9, 19)       # هفته شنبه–جمعه


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


def _book(n=10, title="ریاضی جامع"):
    return {
        "title": title,
        "publisher": "خیلی سبز",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {
                        "title": "تابع",
                        "questions": [{"number": i, "answer": str((i % 4) + 1)} for i in range(1, n + 1)],
                    }
                ],
            }
        ],
    }


def _setup(client, email, taught=True, wrongs=(1, 2, 3, 4, 5)):
    """user + book + taught + یک جلسه با غلط → learning state + صف مرور."""
    u = _user(client, email)
    r = client.post("/api/v1/resources/import-book", json=_book(), headers=_h(u))
    rid = r.json()["data"]["resource"]["id"]
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]
    topic_id = tree["tree"][0]["children"][0]["id"]
    if taught:
        rt = client.put(
            "/api/v1/students/me/taught-topics",
            json={"items": [{"topic_id": topic_id, "taught": True}]},
            headers=_h(u),
        )
        assert rt.status_code == 200, rt.text
    if wrongs:
        s = client.post("/api/v1/test-sessions", json={"resource_id": rid}, headers=_h(u)).json()["data"]
        qid = {q["number"]: q["question_id"] for q in s["questions"]}
        items = [{"question_id": qid[n], "status": "answered", "result": "wrong"} for n in wrongs]
        client.post(f"/api/v1/test-sessions/{s['session']['id']}/records", json={"items": items}, headers=_h(u))
        client.post(f"/api/v1/test-sessions/{s['session']['id']}/finish", json={}, headers=_h(u))
    return u, rid, topic_id


# --- domain (فرمول‌های خالص) -------------------------------------------------------------

def test_domain_pipeline_is_doc_order():
    assert domain.PIPELINE == (
        "load_context", "exams", "goals", "taught_filter", "learning_states", "review_demand",
        "priority_items", "capacity_per_day", "allocate_tasks", "overload_check", "explain",
        "save_suggested",
    )
    assert len(domain.PIPELINE) == 12


def test_domain_capacity_defaults():
    # بدون بلوک → پیش‌فرض روز؛ جمعه ۵۴۰ × ۰٫۷ = ۳۷۸ دقیقه
    cap = domain.compute_capacity(free_minutes=0, weekday=6, has_blocks=False, done_7d=0, total_7d=0)
    assert cap["available_minutes"] == 378
    assert cap["suggested_task_count"] == round(378 / 45)
    assert cap["suggested_session_count"] == min(round(378 / 90), 378 // 60)
    assert cap["completion_rate"] == 0.7  # بدون سابقه → پیش‌فرض

    # سابقه واقعی جای پیش‌فرض را می‌گیرد
    cap2 = domain.compute_capacity(free_minutes=0, weekday=0, has_blocks=False, done_7d=1, total_7d=2)
    assert cap2["available_minutes"] == round(240 * 0.5)


def test_domain_state_factor_low_weight():
    assert domain.state_factor(None, None) == 1.0
    assert domain.state_factor(3, 3) == 1.0
    f = domain.state_factor(5, 5)
    assert 1.0 < f <= 1.15  # وزن پایین، کران‌دار
    assert domain.state_factor(1, 1) >= 0.85


def test_domain_spread_recovery_no_dump_v2_p04():
    days = ["2026-09-20", "2026-09-21", "2026-09-22"]
    tasks = [{"id": f"t{i}", "critical": False} for i in range(6)]
    spread = domain.spread_recovery(tasks, days)
    assert sum(len(v) for v in spread.values()) == 6
    assert len(spread[days[0]]) <= 2  # همه روی فردا/امروز انباشته نمی‌شود
    assert len(spread[days[1]]) == 2 and len(spread[days[2]]) == 2

    # critical اولویت روز زودتر دارد ولی بقیه پخش می‌شوند
    tasks2 = [{"id": "c1", "critical": True}, {"id": "n1", "critical": False}, {"id": "n2", "critical": False}]
    sp2 = domain.spread_recovery(tasks2, days)
    assert sp2[days[0]][0]["id"] == "c1"
    assert len(sp2[days[0]]) <= 2


def test_domain_overload_trim_priority():
    tasks = [
        {"kind": "study", "minutes": 45, "title": "s"},
        {"kind": "review", "minutes": 30, "title": "r"},
        {"kind": "test", "minutes": 60, "title": "t"},
    ]
    keep, trimmed = domain.overload_trim(tasks, task_cap=2, available_minutes=1000)
    assert {k["kind"] for k in keep} == {"review", "test"}  # study اول حذف می‌شود
    assert trimmed[0]["kind"] == "study"


def test_domain_recommendation_has_reason():
    rec = domain.recommendation_pick([], [], [])
    assert rec["reasons"] == ["no_demand"]
    rec2 = domain.recommendation_pick([{"id": "x", "status": "pending", "title": "t", "minutes": 30, "reason_code": "weakness"}], [], [])
    assert rec2["payload"]["kind"] == "task"
    assert "today_task" in rec2["reasons"] and "weakness" in rec2["reasons"]
    rec3 = domain.recommendation_pick([], [{"id": "r", "critical": True}], [])
    assert rec3["reasons"] == ["review_critical"]


# --- capacity & school override (V2-P02) ---------------------------------------------------

def test_capacity_default_and_blocks(client):
    u, _rid, _t = _setup(client, "pl1@example.com", taught=False, wrongs=())
    c0 = client.get("/api/v1/capacity", headers=_h(u)).json()["data"]
    # یکشنبه بدون بلوک → پیش‌فرض ۲۴۰ × ۰٫۷ = ۱۶۸
    assert c0["available_minutes"] == 168
    assert c0["suggested_session_count"] == 2  # وعده ۶۰–۱۲۰ دقیقه
    assert c0["weekday_fa"] == "یکشنبه"

    r = client.put(
        "/api/v1/time-blocks",
        json={"date": "1405/06/29", "blocks": [
            {"kind": "school", "start": "07:00", "end": "14:00", "title": "مدرسه"},
            {"kind": "free", "start": "16:00", "end": "20:00"},
        ]},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["capacity"]["school_minutes"] == 420
    assert d["capacity"]["available_minutes"] == round(240 * 0.7)  # free صریح ۲۴۰

    g = client.get("/api/v1/time-blocks?date=1405-06-29", headers=_h(u)).json()["data"]
    assert len(g["blocks"]) == 2
    assert g["blocks"][0]["start"] == "07:00"


def test_school_override_changes_capacity_v2_p02(client):
    u, _rid, _t = _setup(client, "pl2@example.com", taught=False, wrongs=())
    before = client.get("/api/v1/capacity?date=2026-09-20", headers=_h(u)).json()["data"]

    r = client.post(
        "/api/v1/school-override",
        json={"date": "2026-09-20", "blocks": [{"kind": "school", "start": "08:00", "end": "13:00"}]},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    after = r.json()["data"]
    assert after["capacity"]["source"] == "override"
    # روز فقط-مدرسه (بدون بلوک آزاد) → ظرفیت مطالعه صفر می‌شود: override ظرفیت را عوض کرد
    assert after["capacity"]["available_minutes"] != before["available_minutes"]
    assert after["capacity"]["available_minutes"] == 0
    assert after["capacity"]["school_minutes"] == 300

    # تعطیلی مدرسه → بلوک مدرسه حذف، ظرفیت برمی‌گردد
    off = client.post("/api/v1/school-override", json={"date": "2026-09-20", "school_off": True}, headers=_h(u))
    assert off.status_code == 200
    assert off.json()["data"]["capacity"]["available_minutes"] == before["available_minutes"]

    # خطا: override بدون بلوک و بدون تعطیلی
    bad = client.post("/api/v1/school-override", json={"date": "2026-09-20"}, headers=_h(u))
    assert bad.status_code == 422
    assert "بلوک‌های مدرسه" in bad.json()["error"]["message"]


# --- generate week (doc 11.3) ---------------------------------------------------------------

def test_generate_week_pipeline_logged_and_suggested(client):
    u, _rid, topic_id = _setup(client, "pl3@example.com")
    r = client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["week_start"] == "2026-09-19"  # شنبه
    assert [s["step"] for s in d["steps"]] == list(domain.PIPELINE)  # همان ترتیب، لاگ‌شده

    # مرور امروز (۵ غلط سررسید امروز) → task مرور
    sunday = [x for x in d["days"] if x["date"] == "2026-09-20"][0]
    assert sunday["tasks_count"] >= 1
    plan = client.get("/api/v1/plans/2026-09-20", headers=_h(u)).json()["data"]
    kinds = {t["kind"] for t in plan["tasks"]}
    assert "review" in kinds
    rev = [t for t in plan["tasks"] if t["kind"] == "review"][0]
    assert rev["count"] == 5
    assert rev["reason_fa"]  # explain مرحله ۱۱ — دلیل فارسی

    # taught filter → priority شامل موضوع تدریس‌شده
    assert any(p["topic_id"] == topic_id for p in d["priority"])
    assert d["priority"][0]["score"] > 0

    # مرحله ۱۲: suggested نه locked
    assert all(t["locked"] is False and t["source"] == "generated" for t in plan["tasks"])
    assert d["created"] >= 2


def test_generate_week_without_taught_still_runs(client):
    u, _rid, _t = _setup(client, "pl4@example.com", taught=False)
    r = client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert len(d["steps"]) == 12
    assert d["priority"] == []  # practice روی taught=false بدون تأیید صریح (doc 08 §8.8)
    # مرور از taught مستقل است → task مرور ساخته می‌شود
    assert d["created"] >= 1


def test_locked_task_survives_regenerate_v2_p03(client):
    u, _rid, _t = _setup(client, "pl5@example.com")
    client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))
    plan = client.get("/api/v1/plans/2026-09-19", headers=_h(u)).json()["data"]
    assert plan["tasks"], "شنبه باید کار تولیدشده داشته باشد"
    victim = plan["tasks"][0]

    # قفل (pin/lock — doc 11.4)
    lk = client.post(f"/api/v1/plans/tasks/{victim['id']}/lock", json={"locked": True}, headers=_h(u))
    assert lk.status_code == 200
    assert lk.json()["data"]["locked"] is True

    # کار دستی هم اضافه شود
    client.put(
        "/api/v1/plans/2026-09-19",
        json={"tasks": [
            {"id": victim["id"], "locked": True},
            {"title": "خلاصه‌نویسی تابع", "kind": "study", "minutes": 30},
        ]},
        headers=_h(u),
    )

    # regenerate
    r2 = client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))
    assert r2.status_code == 200
    assert r2.json()["data"]["kept_locked"] >= 1

    after = client.get("/api/v1/plans/2026-09-19", headers=_h(u)).json()["data"]
    ids = {t["id"] for t in after["tasks"]}
    locked_after = [t for t in after["tasks"] if t["locked"]]
    assert victim["id"] in ids                      # V2-P03: قفل‌شده ماند
    assert locked_after and locked_after[0]["id"] == victim["id"]
    assert any(t["title"] == "خلاصه‌نویسی تابع" for t in after["tasks"])  # manual هم ماند
    assert any(t["source"] == "generated" for t in after["tasks"])        # بقیه از نو suggested


# --- manual override: add/move/split/merge/count (doc 11.4) ----------------------------------

def test_manual_override_operations(client):
    u, _rid, _t = _setup(client, "pl6@example.com")
    r0 = client.put(
        "/api/v1/plans/1405-06-29",  # تاریخ شمسی هم قبول است
        json={"tasks": [{"title": "تست جامع", "kind": "test", "minutes": 60, "count": 20}]},
        headers=_h(u),
    )
    assert r0.status_code == 200, r0.text
    day = r0.json()["data"]
    t1 = day["tasks"][0]
    assert t1["source"] == "manual" and t1["kind_fa"] == "تست"

    # change count
    upd = client.put(
        "/api/v1/plans/2026-09-20",
        json={"tasks": [{"id": t1["id"], "count": 30, "minutes": 90}]},
        headers=_h(u),
    ).json()["data"]
    assert upd["tasks"][0]["count"] == 30 and upd["tasks"][0]["minutes"] == 90

    # split
    sp = client.post(f"/api/v1/plans/tasks/{t1['id']}/split", json={"parts": [45, 45]}, headers=_h(u))
    assert sp.status_code == 200, sp.text
    parts = sp.json()["data"]["tasks"]
    assert sp.json()["data"]["parts"] == 2
    assert parts[0]["id"] == t1["id"] and parts[0]["minutes"] == 45
    assert parts[1]["minutes"] == 45 and parts[1]["source"] == "manual"

    # merge
    mg = client.post(
        "/api/v1/plans/tasks/merge",
        json={"task_ids": [parts[0]["id"], parts[1]["id"]]},
        headers=_h(u),
    )
    assert mg.status_code == 200, mg.text
    assert mg.json()["data"]["minutes"] == 90

    # move day
    mv = client.post(
        "/api/v1/plans/2026-09-20/move-task",
        json={"task_id": t1["id"], "to_date": "1405/06/30"},
        headers=_h(u),
    )
    assert mv.status_code == 200, mv.text
    assert mv.json()["data"]["date"] == "2026-09-21"
    tues = client.get("/api/v1/plans/2026-09-21", headers=_h(u)).json()["data"]
    assert any(t["id"] == t1["id"] for t in tues["tasks"])

    # remove via PUT (لیست خالی = حذف همه)
    rm = client.put("/api/v1/plans/2026-09-21", json={"tasks": []}, headers=_h(u)).json()["data"]
    assert rm["removed"] >= 1 and rm["tasks"] == []


def test_status_checkbox_flow(client):
    u, _rid, _t = _setup(client, "pl7@example.com")
    day = client.put(
        "/api/v1/plans/2026-09-20", json={"tasks": [{"title": "مطالعه تابع", "minutes": 45}]}, headers=_h(u)
    ).json()["data"]
    tid = day["tasks"][0]["id"]
    r = client.post(f"/api/v1/plans/tasks/{tid}/status", json={"status": "done"}, headers=_h(u))
    assert r.json()["data"]["status"] == "done"
    # completion روی ظرفیت فردا اثر دارد (میانگین هفت روز اخیر)
    cap = client.get("/api/v1/capacity?date=2026-09-21", headers=_h(u)).json()["data"]
    assert cap["completion_rate"] == 1.0  # یک کار، یک انجام


# --- recovery (doc 11.5، V2-P04) ---------------------------------------------------------------

def test_recovery_spreads_without_dump(client):
    u, _rid, _t = _setup(client, "pl8@example.com")
    # شنبه (دیروز) ۶ کار عقب‌افتاده — یکی مرور (بحرانی)
    tasks = [{"title": f"کار {i}", "minutes": 30} for i in range(5)]
    tasks.append({"title": "مرور حیاتی", "kind": "review", "minutes": 30, "reason_code": "review_critical"})
    client.put("/api/v1/plans/2026-09-19", json={"tasks": tasks}, headers=_h(u))

    r = client.post("/api/v1/plans/recover", json={}, headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["moved"] == 6
    assert d["tomorrow_share"] == d["days"]["2026-09-20"]
    assert d["tomorrow_share"] < d["moved"]          # V2-P04: همه روی فردا/امروز نمی‌ریزد
    assert sum(d["days"].values()) == 6
    assert len([v for v in d["days"].values() if v > 0]) >= 3  # پخش در روزهای باقی‌مانده

    # بحرانی اولویت روز زودتر را حفظ کرد
    today_plan = client.get("/api/v1/plans/2026-09-20", headers=_h(u)).json()["data"]
    titles = [t["title"] for t in today_plan["tasks"]]
    assert "مرور حیاتی" in titles
    moved = [t for t in today_plan["tasks"] if t["title"] == "مرور حیاتی"][0]
    assert moved["source"] == "recovered"

    # شنبه خالی شد
    sat = client.get("/api/v1/plans/2026-09-19", headers=_h(u)).json()["data"]
    assert sat["tasks"] == []


# --- today hub (doc 11.1، V2-P01) -------------------------------------------------------------

def test_today_full_shape_v2_p01(client):
    u, _rid, topic_id = _setup(client, "pl9@example.com")
    client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))

    r = client.get("/api/v1/today", headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]

    # doc 11.1 — همه بخش‌ها
    for key in ("checkin", "capacity", "plan_items", "review_top", "upcoming_exams", "recommendation", "week_sparkline"):
        assert key in d, key
    assert d["date"] == "2026-09-20" and d["date_jalali"] == "1405/06/29"
    assert d["weekday_fa"] == "یکشنبه"
    assert d["greeting"] in ("صبح بخیر", "ظهر بخیر", "عصر بخیر", "شب بخیر")

    assert d["checkin"]["today"] is None or isinstance(d["checkin"]["today"], dict)
    assert d["review_due_count"] == 5 and len(d["review_top"]) == 5
    assert d["upcoming_exams"] == []  # فاز ۶
    assert len(d["week_sparkline"]) == 7
    assert d["week_sparkline"][-1]["is_today"] is True
    assert d["week"]["week_start"] == "2026-09-19" and len(d["week"]["days"]) == 7

    # recommendation با reason فارسی (doc 08 §8.10)
    rec = d["recommendation"]
    assert rec is not None and rec["status"] == "suggested"
    assert len(rec["reasons"]) >= 1
    assert all(x["code"] and x["fa"] for x in rec["reasons"])

    # idempotent — همان rec امروز برمی‌گردد
    r2 = client.get("/api/v1/recommendations/today", headers=_h(u)).json()["data"]
    assert r2["id"] == rec["id"]

    # respond
    acc = client.post(f"/api/v1/recommendations/{rec['id']}/respond", json={"status": "accepted"}, headers=_h(u))
    assert acc.json()["data"]["status"] == "accepted"
    rej = client.post(f"/api/v1/recommendations/{rec['id']}/respond", json={"status": "rejected"}, headers=_h(u))
    assert rej.json()["data"]["status"] == "rejected"

    # 404 فارسی
    nf = client.post("/api/v1/recommendations/nope/respond", json={"status": "accepted"}, headers=_h(u))
    assert nf.status_code == 404 and nf.json()["error"]["message"] == "پیشنهاد پیدا نشد."


def test_today_with_checkin_state_weight(client):
    u, _rid, _t = _setup(client, "pl10@example.com", taught=False, wrongs=())
    client.post(
        "/api/v1/students/me/checkin",
        json={"energy": 5, "focus": 5, "motivation": 4, "stress": 2, "fatigue": 1},
        headers=_h(u),
    )
    d = client.get("/api/v1/today", headers=_h(u)).json()["data"]
    assert d["checkin"]["today"]["energy"] == 5
    assert d["capacity"]["state_factor"] > 1.0  # انرژی بالا → ظرفیت کمی بیشتر (وزن پایین)


# --- priority & goals -------------------------------------------------------------------------

def test_priority_week_snapshot(client):
    u, _rid, topic_id = _setup(client, "pl11@example.com")
    client.post("/api/v1/plans/generate-week", json={}, headers=_h(u))
    r = client.get("/api/v1/priority/week", headers=_h(u))
    assert r.status_code == 200
    d = r.json()["data"]
    assert d["from_snapshot"] is True and d["week_start"] == "2026-09-19"
    assert any(it["topic_id"] == topic_id for it in d["items"])


def test_goals_crud(client):
    u = _user(client, "pl12@example.com")
    r = client.post(
        "/api/v1/goals",
        json={"title": "پوشش کامل تابع", "kind": "week", "target_date": "1405/07/03"},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    g = r.json()["data"]
    assert g["target_date_jalali"] == "1405/07/03"

    lst = client.get("/api/v1/goals", headers=_h(u)).json()["data"]["items"]
    assert len(lst) == 1

    bad = client.post("/api/v1/goals", json={"title": "  ", "kind": "week"}, headers=_h(u))
    assert bad.status_code == 422
    assert bad.json()["error"]["message"] == "عنوان هدف نمی‌تواند خالی باشد."

    dele = client.delete(f"/api/v1/goals/{g['id']}", headers=_h(u))
    assert dele.status_code == 200
    assert client.get("/api/v1/goals", headers=_h(u)).json()["data"]["items"] == []


# --- خطاها ----------------------------------------------------------------------------------

def test_planning_persian_errors(client):
    u = _user(client, "pl13@example.com")

    bad_date = client.get("/api/v1/plans/xx-yy", headers=_h(u))
    assert bad_date.status_code == 422 and bad_date.json()["error"]["message"] == "تاریخ نامعتبر است."

    bad_time = client.put(
        "/api/v1/time-blocks",
        json={"date": "2026-09-20", "blocks": [{"kind": "free", "start": "not-a-time", "end": "10:00"}]},
        headers=_h(u),
    )
    assert bad_time.status_code == 422 and bad_time.json()["error"]["message"] == "زمان را مثل ۰۸:۳۰ وارد کن."

    end_first = client.put(
        "/api/v1/time-blocks",
        json={"date": "2026-09-20", "blocks": [{"kind": "free", "start": "18:00", "end": "10:00"}]},
        headers=_h(u),
    )
    assert end_first.status_code == 422
    assert end_first.json()["error"]["message"] == "ساعت پایان باید بعد از شروع باشد."

    split_bad = client.post("/api/v1/plans/tasks/nope/split", json={"parts": [5, 5]}, headers=_h(u))
    assert split_bad.status_code == 404 and split_bad.json()["error"]["message"] == "کار برنامه پیدا نشد."

    merge_one = client.post("/api/v1/plans/tasks/merge", json={"task_ids": ["a"]}, headers=_h(u))
    assert merge_one.status_code == 422  # schema min_length=2

    unauth = client.get("/api/v1/today")
    assert unauth.status_code == 401 and unauth.json()["error"]["message"] == "برای ادامه باید وارد شوید."
