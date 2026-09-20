"""Phase 4 — Review & Learning (doc 10, doc 08 §8.4, doc 15 V2-R01..R04).

- صف از wrong/marks (+blank اختیاری از settings)
- چرخه ۱-۳-۷-۱۴ از settings؛ complete → scheduled بعدی؛ پایان چرخه → absorbed
- postpone (V2-R04) · critical برای غلط ≥۲ (V2-R03)
- cluster suggestion: سقف روزانه + خوشه ≥ min_cluster با هم
- learning_states per topic + weakness (doc 10 §10.4-10.5)
- rebuild خودکار با event بعد از finish تست
"""
from __future__ import annotations

import datetime as dt

from app.core.jalali import today_jalali
from app.modules.review import domain

PASS = "pass1234"
# لنگر تقویم تست‌ها: از ساعت زنده خود اپ (Asia/Tehran) مشتق می‌شود — دقیقاً همان
# «امروز» که API برای scheduled_date استفاده می‌کند. لیترال ثابت (مثلاً
# dt.date(2026, 9, 20)) با عبور از نیمه‌شب تهران کهنه می‌شد و تست‌های مسیر زنده
# را به‌غلط قرمز می‌کرد (time bomb). تست‌های خالص domain همچنان تاریخ را صریح
# پاس می‌دهند و خودسازگارند.
TODAY_TEHRAN = today_jalali().to_gregorian()


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


def _setup(client, email, n=10):
    u = _user(client, email)
    r = client.post("/api/v1/resources/import-book", json=_book(n), headers=_h(u))
    assert r.status_code == 200, r.text
    rid = r.json()["data"]["resource"]["id"]
    return u, rid


def _session(client, u, rid, marks: dict[int, str], numbers=None):
    """marks: {question_number: 'correct'|'wrong'|'blank'} → create+records+finish."""
    r = client.post("/api/v1/test-sessions", json={"resource_id": rid}, headers=_h(u))
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    sid = data["session"]["id"]
    qid = {q["number"]: q["question_id"] for q in data["questions"]}
    items = []
    for n, res in marks.items():
        if res == "blank":
            items.append({"question_id": qid[n], "status": "unanswered"})
        else:
            items.append({"question_id": qid[n], "status": "answered", "result": res})
    if items:
        rr = client.post(f"/api/v1/test-sessions/{sid}/records", json={"items": items}, headers=_h(u))
        assert rr.status_code == 200, rr.text
    rf = client.post(f"/api/v1/test-sessions/{sid}/finish", json={}, headers=_h(u))
    assert rf.status_code == 200, rf.text
    return sid, qid


def _queue(client, u):
    r = client.get("/api/v1/reviews/queue", headers=_h(u))
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _put_settings(client, u, payload):
    r = client.put("/api/v1/settings", json=payload, headers=_h(u))
    assert r.status_code == 200, r.text


DEFAULTS = {
    "review_intervals": [1, 3, 7, 14],
    "include_blank_in_review": False,
    "max_daily_review": 25,
    "min_cluster": 8,
}


# --- domain (فرمول‌های خالص، doc 10 §10.4: قابل‌تست و بدون hard-code پراکنده) ----------

def test_domain_cycle_default_intervals():
    nxt = domain.next_after_complete(0, [1, 3, 7, 14], TODAY_TEHRAN)
    assert nxt["status"] == "scheduled" and nxt["cycle_index"] == 1
    assert nxt["scheduled_date"] == TODAY_TEHRAN + dt.timedelta(days=1)
    assert nxt["next_interval_days"] == 3

    nxt = domain.next_after_complete(3, [1, 3, 7, 14], TODAY_TEHRAN)
    assert nxt["scheduled_date"] == TODAY_TEHRAN + dt.timedelta(days=14)
    assert nxt["next_interval_days"] is None

    done = domain.next_after_complete(4, [1, 3, 7, 14], TODAY_TEHRAN)
    assert done["status"] == "absorbed" and done["scheduled_date"] is None


def test_domain_learning_state_formulas():
    # بدون داده → همه صفر، confidence صفر، weakness false
    empty = domain.learning_state(0, 0, 0, 0, 0, 0, None, [])
    assert empty["coverage"] == 0.0 and empty["confidence"] == 0.0 and empty["weakness"] is False

    # recency: امروز ۱، نیمه‌عمر ۷ روز → ۰٫۵
    assert domain.compute_recency(0) == 1.0
    assert domain.compute_recency(7) == 0.5

    # accuracy = C/(C+W) — doc 08 §8.5
    assert domain.compute_accuracy(3, 1) == 0.75

    # exam_readiness وزن‌ها: همه ۱ → ۱
    assert domain.compute_exam_readiness(1, 1, 1, 0) == 1.0

    # weakness ترکیبی است نه تک‌سیگنال (doc 10 §10.5)
    assert domain.is_weakness(coverage=0.4, accuracy=0.2, repeated_error=0.5, confidence=0.8, has_evidence=True)
    assert not domain.is_weakness(coverage=1.0, accuracy=0.2, repeated_error=0.5, confidence=0.8, has_evidence=True)
    assert not domain.is_weakness(coverage=0.4, accuracy=0.2, repeated_error=0.5, confidence=0.1, has_evidence=True)


def test_domain_cluster_pick_prefers_big_cluster_and_respects_budget():
    items = [
        {"id": f"a{i}", "topic_id": "TA", "critical": i == 0, "wrong_count": 1, "scheduled_date": TODAY_TEHRAN}
        for i in range(10)
    ] + [
        {"id": f"b{i}", "topic_id": "TB", "critical": False, "wrong_count": 1, "scheduled_date": TODAY_TEHRAN}
        for i in range(3)
    ]
    # خوشه ۱۰تایی ≥ min_cluster=8 → با هم انتخاب می‌شود
    picked = domain.pick_cluster_suggestion(items, TODAY_TEHRAN, budget=25, min_cluster=8)
    assert {p["id"] for p in picked} >= {f"a{i}" for i in range(10)}

    # بودجه ۵ → خوشه بزرگ جا نمی‌شود؛ با اولویت (critical اول) پر می‌شود
    picked5 = domain.pick_cluster_suggestion(items, TODAY_TEHRAN, budget=5, min_cluster=8)
    assert len(picked5) == 5
    assert picked5[0]["critical"] is True


# --- صف مرور ---------------------------------------------------------------------

def test_queue_built_automatically_by_finish_event(client):
    """rebuild با event بعد از finish تست — بدون فراخوانی دستی rebuild."""
    u, rid = _setup(client, "rev1@example.com")
    _session(client, u, rid, {1: "wrong", 2: "wrong", 3: "correct", 4: "blank"})

    q = _queue(client, u)
    assert q["due_count"] == 2  # فقط wrongها (blank پیش‌فرض خاموش)
    by_num = {it["number"]: it for it in q["items"]}
    assert set(by_num) == {1, 2}
    it = by_num[1]
    assert it["source"] == "wrong" and it["source_fa"] == "غلط"
    assert it["critical"] is False and it["wrong_count"] == 1  # هنوز یک غلط
    assert it["status"] == "pending"
    assert it["cycle_index"] == 0 and it["cycle_length"] == 4 and it["next_interval_days"] == 1
    assert it["scheduled_date_jalali"] == today_jalali().format()
    assert it["book_title"] == "ریاضی جامع" and it["topic_title"] == "تابع"
    assert it["your_answer"] is None and it["correct_answer"] == "2"


def test_critical_when_wrong_count_ge_2_v2_r03(client):
    u, rid = _setup(client, "rev2@example.com")
    _session(client, u, rid, {1: "wrong"})
    q1 = _queue(client, u)
    item = q1["items"][0]
    assert item["critical"] is False

    _session(client, u, rid, {1: "wrong"})  # جلسه دوم، همان سوال دوباره غلط
    q2 = _queue(client, u)
    item2 = [i for i in q2["items"] if i["number"] == 1][0]
    assert item2["critical"] is True        # V2-R03: غلط ≥ ۲ → critical
    assert item2["wrong_count"] == 2
    assert item2["id"] == item["id"]        # همان آیتم — duplicate ساخته نشد
    assert q2["due_count"] == 1


def test_marks_enter_queue_v2_r01(client):
    from app.core.events import QUESTION_MARKS_CHANGED, event_bus

    u, rid = _setup(client, "rev3@example.com")
    sid, qid = _session(client, u, rid, {3: "correct"})

    got: list = []
    handler = got.append
    event_bus.subscribe(QUESTION_MARKS_CHANGED, handler)
    try:
        r = client.put(
            f"/api/v1/questions/{qid[3]}/marks", json={"review": True}, headers=_h(u)
        )
    finally:
        event_bus.unsubscribe(QUESTION_MARKS_CHANGED, handler)
    assert r.status_code == 200, r.text
    assert r.json()["data"]["review"] is True
    assert len(got) == 1 and got[0].payload["question_id"] == qid[3]

    q = _queue(client, u)  # V2-R01: تیک review → ورود به صف
    assert q["due_count"] == 1
    it = q["items"][0]
    assert it["source"] == "mark_review" and it["source_fa"] == "تیک مرور"
    assert it["marks"] == {"review": True, "important": False, "hard": False}

    g = client.get(f"/api/v1/questions/{qid[3]}/marks", headers=_h(u))
    assert g.json()["data"]["review"] is True


def test_blank_queue_from_settings(client):
    u, rid = _setup(client, "rev4@example.com")
    _session(client, u, rid, {4: "blank"})
    assert _queue(client, u)["due_count"] == 0  # پیش‌فرض: blank وارد صف نمی‌شود

    _put_settings(client, u, {"include_blank_in_review": True})
    try:
        client.post("/api/v1/reviews/rebuild", headers=_h(u))
        q = _queue(client, u)
        assert q["due_count"] == 1
        assert q["items"][0]["source"] == "blank" and q["items"][0]["source_fa"] == "نزده"
    finally:
        _put_settings(client, u, {"include_blank_in_review": False})


def test_complete_walks_cycle_1_3_7_14_then_absorbed(client):
    u, rid = _setup(client, "rev5@example.com")
    _session(client, u, rid, {1: "wrong"})
    item = _queue(client, u)["items"][0]
    today = TODAY_TEHRAN

    expected_days = [1, 3, 7, 14]
    for idx, days in enumerate(expected_days, start=1):
        r = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u))
        assert r.status_code == 200, r.text
        d = r.json()["data"]
        assert d["status"] == "scheduled"
        assert d["cycle_index"] == idx
        assert d["review_count"] == idx
        assert dt.date.fromisoformat(d["scheduled_date"]) == today + dt.timedelta(days=days)

    # V2-R02 semantics: پس از اتمام چرخه، complete آخر → absorbed
    r = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u))
    d = r.json()["data"]
    assert d["status"] == "absorbed" and d["scheduled_date"] is None

    q = _queue(client, u)
    assert q["due_count"] == 0 and q["absorbed_count"] == 1


def test_complete_uses_custom_intervals_from_settings(client):
    u, rid = _setup(client, "rev6@example.com")
    _put_settings(client, u, {"review_intervals": [1, 2]})
    try:
        _session(client, u, rid, {1: "wrong"})
        item = _queue(client, u)["items"][0]
        assert item["cycle_length"] == 2

        d1 = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u)).json()["data"]
        assert dt.date.fromisoformat(d1["scheduled_date"]) == TODAY_TEHRAN + dt.timedelta(days=1)
        d2 = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u)).json()["data"]
        assert dt.date.fromisoformat(d2["scheduled_date"]) == TODAY_TEHRAN + dt.timedelta(days=2)
        d3 = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u)).json()["data"]
        assert d3["status"] == "absorbed"
    finally:
        _put_settings(client, u, {"review_intervals": [1, 3, 7, 14]})


def test_postpone_moves_date_status_pending_v2_r04(client):
    u, rid = _setup(client, "rev7@example.com")
    _session(client, u, rid, {1: "wrong"})
    item = _queue(client, u)["items"][0]

    r = client.post(f"/api/v1/reviews/{item['id']}/postpone", json={}, headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["status"] == "pending"
    assert dt.date.fromisoformat(d["scheduled_date"]) == TODAY_TEHRAN + dt.timedelta(days=1)

    r2 = client.post(f"/api/v1/reviews/{item['id']}/postpone", json={"days": 3}, headers=_h(u))
    d2 = r2.json()["data"]
    assert dt.date.fromisoformat(d2["scheduled_date"]) == TODAY_TEHRAN + dt.timedelta(days=4)
    assert d2["status"] == "pending"


def test_rebuild_idempotent_no_duplicates(client):
    u, rid = _setup(client, "rev8@example.com")
    _session(client, u, rid, {1: "wrong", 2: "wrong"})
    r1 = client.post("/api/v1/reviews/rebuild", headers=_h(u))
    assert r1.status_code == 200
    r2 = client.post("/api/v1/reviews/rebuild", headers=_h(u))
    d2 = r2.json()["data"]
    assert d2["added"] == 0  # duplicate ساخته نمی‌شود
    assert d2["active"] == 2
    assert _queue(client, u)["due_count"] == 2


def test_absorbed_returns_only_with_new_wrong(client):
    u, rid = _setup(client, "rev9@example.com")
    _put_settings(client, u, {"review_intervals": [1]})
    try:
        _session(client, u, rid, {1: "wrong"})
        item = _queue(client, u)["items"][0]
        client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u))
        d = client.post(f"/api/v1/reviews/{item['id']}/complete", json={}, headers=_h(u)).json()["data"]
        assert d["status"] == "absorbed"

        client.post("/api/v1/reviews/rebuild", headers=_h(u))
        assert _queue(client, u)["absorbed_count"] == 1  # بدون غلط جدید برنمی‌گردد

        # غلط جدید در جلسه جدید → خودکار (event) برمی‌گردد
        _session(client, u, rid, {1: "wrong"})
        q = _queue(client, u)
        assert q["due_count"] == 1
        it = q["items"][0]
        assert it["status"] == "pending" and it["cycle_index"] == 0 and it["review_count"] == 0
        assert it["wrong_count"] == 2 and it["critical"] is True
    finally:
        _put_settings(client, u, {"review_intervals": [1, 3, 7, 14]})


# --- cluster -------------------------------------------------------------------------

def test_cluster_suggestion_budget_and_cluster(client):
    u, rid = _setup(client, "rev10@example.com")
    wrongs = {i: "wrong" for i in range(1, 11)}
    _session(client, u, rid, wrongs)

    r = client.get("/api/v1/reviews/cluster-suggestion", headers=_h(u))
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["due_count"] == 10
    assert d["clusters"][0]["topic_title"] == "تابع"
    assert d["clusters"][0]["size"] == 10
    # خوشه ۱۰ ≥ min_cluster=8 و بودجه ۲۵ → همه با هم پیشنهاد می‌شوند
    assert d["suggested_count"] == 10
    assert d["clusters"][0]["suggested_count"] == 10

    _put_settings(client, u, {"max_daily_review": 5})
    try:
        d2 = client.get("/api/v1/reviews/cluster-suggestion", headers=_h(u)).json()["data"]
        assert d2["suggested_count"] == 5  # سقف روزانه رعایت می‌شود
        assert d2["budget"] == 5
    finally:
        _put_settings(client, u, {"max_daily_review": 25})


def test_cluster_suggestion_critical_first(client):
    u, rid = _setup(client, "rev11@example.com")
    _session(client, u, rid, {i: "wrong" for i in range(1, 10)})
    _session(client, u, rid, {5: "wrong"})  # سوال ۵ دو بار غلط → critical
    _put_settings(client, u, {"max_daily_review": 3, "min_cluster": 50})
    try:
        d = client.get("/api/v1/reviews/cluster-suggestion", headers=_h(u)).json()["data"]
        assert d["suggested_count"] == 3
        assert d["suggested"][0]["number"] == 5
        assert d["suggested"][0]["critical"] is True
    finally:
        _put_settings(client, u, {"max_daily_review": 25, "min_cluster": 8})


# --- learning states ---------------------------------------------------------------------

def test_learning_states_and_weakness(client):
    u, rid = _setup(client, "rev12@example.com")
    # پوشش ناقص (۴ از ۱۰) + همه غلط + تکراری → weakness (doc 10 §10.5)
    _session(client, u, rid, {i: "wrong" for i in range(1, 5)})
    _session(client, u, rid, {i: "wrong" for i in range(1, 5)})

    r = client.get("/api/v1/reviews/learning-states", headers=_h(u))
    assert r.status_code == 200, r.text
    items = r.json()["data"]["items"]
    assert len(items) == 1
    st = items[0]
    assert st["topic_title"] == "تابع"
    assert st["total_questions"] == 10
    assert st["attempted_questions"] == 4
    assert st["coverage"] == 0.4
    assert st["accuracy"] == 0.0
    assert st["repeated_error_score"] == 1.0
    assert 0.0 <= st["exam_readiness"] <= 1.0
    assert st["confidence"] >= 0.3
    assert st["weakness"] is True
    assert st["correct_count"] == 0 and st["wrong_count"] == 8


def test_learning_state_not_weak_on_single_wrong(client):
    """doc 10 §10.5 — ضعف «فقط آخرین تست غلط» نیست."""
    u, rid = _setup(client, "rev13@example.com")
    _session(client, u, rid, {1: "wrong", 2: "correct", 3: "correct", 4: "correct", 5: "correct"})
    st = client.get("/api/v1/reviews/learning-states", headers=_h(u)).json()["data"]["items"][0]
    assert st["weakness"] is False
    assert st["accuracy"] == 0.8
    assert st["exam_readiness"] > 0.3


# --- خطاها -------------------------------------------------------------------------------

def test_review_404_and_401_persian(client):
    u, rid = _setup(client, "rev14@example.com")
    r = client.post("/api/v1/reviews/nope/complete", json={}, headers=_h(u))
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "آیتم مرور پیدا نشد."

    r2 = client.get("/api/v1/reviews/queue")
    assert r2.status_code == 401
    assert r2.json()["error"]["message"] == "برای ادامه باید وارد شوید."
