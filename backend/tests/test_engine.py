"""Phase 3 — Test Engine (doc 08 §8.1-8.2, doc 09 §9.2-9.4, doc 15 V2-T01..T05).

پذیرش: نمونه درصد کنکوری استاندارد + past import با not_entered.
"""
from __future__ import annotations

PASS = "pass1234"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


def _book_with_questions(title="ریاضی جامع", n=10):
    """یک فصل، یک موضوع، n سوال با کلیدهای قطعی: سوال i → پاسخ str((i % 4) + 1)."""
    return {
        "title": title,
        "publisher": "خیلی سبز",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {
                        "title": "تابع",
                        "questions": [
                            {"number": i, "answer": str((i % 4) + 1), "difficulty": (i % 5) + 1}
                            for i in range(1, n + 1)
                        ],
                    }
                ],
            }
        ],
    }


def _setup(client, email, book=None):
    u = _user(client, email)
    b = book if book is not None else _book_with_questions()
    r = client.post("/api/v1/resources/import-book", json=b, headers=_h(u))
    assert r.status_code == 200, r.text
    rid = r.json()["data"]["resource"]["id"]
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    topic = tree[0]["children"][0]
    return u, rid, topic


# --- preview + انتخاب بازه -------------------------------------------------------

def test_preview_range_parity(client):
    u, rid, topic = _setup(client, "prev1@example.com")
    r = client.get(
        f"/api/v1/test-engine/preview?resource_id={rid}&from=3&to=8&parity=odd", headers=_h(u)
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["available_in_scope"] == 10
    assert data["matching"] == 3
    assert data["numbers"] == [3, 5, 7]
    assert data["message"] is None


def test_preview_topic_selection_includes_descendants(client):
    u, rid, topic = _setup(client, "prev2@example.com")
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    chapter_id = tree[0]["id"]  # فصل = structural؛ سوال‌ها زیر نوه‌اند
    r = client.get(
        f"/api/v1/test-engine/preview?resource_id={rid}&topic_ids={chapter_id}", headers=_h(u)
    )
    assert r.json()["data"]["matching"] == 10


def test_preview_zero_remaining_message(client):
    u, rid, topic = _setup(client, "prev3@example.com")
    r = client.get(f"/api/v1/test-engine/preview?resource_id={rid}&from=50&to=60", headers=_h(u))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["matching"] == 0
    # doc 09 §9.2 — پیام اجباری
    assert data["message"] == "فقط ۱۰ سوال با این شرایط وجود دارد."


# --- create session ---------------------------------------------------------------

def test_create_session_range_odd_only_v2_t01(client):
    u, rid, topic = _setup(client, "s1@example.com")
    r = client.post(
        "/api/v1/test-sessions",
        json={"mode": "untimed", "resource_id": rid, "from_number": 1, "to_number": 10, "parity": "odd"},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    session = data["session"]
    assert session["mode"] == "untimed"
    assert session["total_count"] == 5
    assert session["finished"] is False
    numbers = [q["number"] for q in data["questions"]]
    assert numbers == [1, 3, 5, 7, 9]  # V2-T01: range + odd → فقط فردها
    # کلید پاسخ قبل از finish لو نمی‌رود
    assert all(q["correct_answer"] is None for q in data["questions"])


def test_create_session_even_and_count_and_difficulty(client):
    u, rid, topic = _setup(client, "s2@example.com")
    r = client.post(
        "/api/v1/test-sessions",
        json={"resource_id": rid, "parity": "even", "count": 2},
        headers=_h(u),
    )
    assert r.json()["data"]["session"]["total_count"] == 2
    numbers = [q["number"] for q in r.json()["data"]["questions"]]
    assert numbers == [2, 4]

    # difficulty=3 → سوال‌های 2،7 (i%5+1==3 → i=2,7)
    r2 = client.post("/api/v1/test-sessions", json={"resource_id": rid, "difficulty": 3}, headers=_h(u))
    nums = sorted(q["number"] for q in r2.json()["data"]["questions"])
    assert nums == [2, 7]


def test_create_session_zero_remaining_422(client):
    u, rid, topic = _setup(client, "s3@example.com")
    r = client.post(
        "/api/v1/test-sessions", json={"resource_id": rid, "from_number": 50, "to_number": 60}, headers=_h(u)
    )
    assert r.status_code == 422
    assert r.json()["error"]["message"] == "فقط ۱۰ سوال با این شرایط وجود دارد."


def test_timed_requires_planned_duration(client):
    u, rid, topic = _setup(client, "s4@example.com")
    r = client.post("/api/v1/test-sessions", json={"mode": "timed", "resource_id": rid}, headers=_h(u))
    assert r.status_code == 422
    assert "زمان‌دار" in r.json()["error"]["message"]

    r2 = client.post(
        "/api/v1/test-sessions",
        json={"mode": "timed", "resource_id": rid, "planned_duration": 600},
        headers=_h(u),
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["session"]["planned_duration"] == 600


def test_bad_range_422(client):
    u, rid, topic = _setup(client, "s5@example.com")
    r = client.post(
        "/api/v1/test-sessions", json={"resource_id": rid, "from_number": 8, "to_number": 3}, headers=_h(u)
    )
    assert r.status_code == 422
    assert "شماره شروع" in r.json()["error"]["message"]


# --- records + append-only + finish ---------------------------------------------------

def _create(client, u, rid, **kw):
    r = client.post("/api/v1/test-sessions", json={"resource_id": rid, **kw}, headers=_h(u))
    assert r.status_code == 200, r.text
    return r.json()["data"]


def test_records_upsert_scoring_and_append_only_history_v2_t05(client):
    u, rid, topic = _setup(client, "r1@example.com")
    data = _create(client, u, rid, from_number=1, to_number=3)
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}

    # سوال ۱ (کلید «2»): اول غلط، بعد اصلاح → تاریخچه append-only، scoring آخرین
    r1 = client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [{"question_id": qs[1], "status": "answered", "answer": "4"}]},
        headers=_h(u),
    )
    assert r1.status_code == 200, r1.text
    assert r1.json()["data"]["progress"]["wrong_count"] == 1

    r2 = client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [{"question_id": qs[1], "status": "answered", "answer": "2"}]},
        headers=_h(u),
    )
    prog = r2.json()["data"]["progress"]
    assert prog["correct_count"] == 1
    assert prog["wrong_count"] == 0

    detail = client.get(f"/api/v1/test-sessions/{sid}", headers=_h(u)).json()["data"]
    q1_attempts = [a for a in detail["attempts"] if a["question_number"] == 1]
    assert len(q1_attempts) == 2  # V2-T05: هر دو ردیف در تاریخچه ماندند
    assert q1_attempts[0]["result"] == "wrong"
    assert q1_attempts[1]["result"] == "correct"
    assert q1_attempts[0]["answer_key_version"] == 1


def test_records_by_number_and_unanswered(client):
    u, rid, topic = _setup(client, "r2@example.com")
    data = _create(client, u, rid, from_number=1, to_number=5)
    sid = data["session"]["id"]
    r = client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={
            "items": [
                {"number": 2, "status": "answered", "result": "correct", "duration_seconds": 45},
                {"number": 4, "status": "unanswered"},
            ]
        },
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    prog = r.json()["data"]["progress"]
    assert prog["correct_count"] == 1
    assert prog["unanswered_count"] == 4  # 1 نزده صریح + 3 ثبت‌نشده

    bad = client.post(
        f"/api/v1/test-sessions/{sid}/records", json={"items": [{"number": 99, "status": "unanswered"}]}, headers=_h(u)
    )
    assert bad.status_code == 422
    assert bad.json()["error"]["message"] == "سوال با این شماره در انتخاب جلسه نیست."


def test_finish_konkur_percent_sample_v2_t04(client):
    """نمونه استاندارد: T=10، C=5، W=3، k=0.33 → (5−0.99)/10×100 = 40.1 و 50.0."""
    u, rid, topic = _setup(client, "f1@example.com")
    data = _create(client, u, rid)  # همه ۱۰ سوال
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}

    items = []
    for n in (1, 2, 3, 4, 5):
        items.append({"question_id": qs[n], "status": "answered", "result": "correct"})
    for n in (6, 7, 8):
        items.append({"question_id": qs[n], "status": "answered", "result": "wrong"})
    items.append({"question_id": qs[9], "status": "unanswered"})
    r = client.post(f"/api/v1/test-sessions/{sid}/records", json={"items": items}, headers=_h(u))
    assert r.status_code == 200, r.text

    fin = client.post(f"/api/v1/test-sessions/{sid}/finish", json={}, headers=_h(u))
    assert fin.status_code == 200, fin.text
    s = fin.json()["data"]["session"]
    assert s["finished"] is True
    assert s["total_count"] == 10
    assert s["correct_count"] == 5
    assert s["wrong_count"] == 3
    assert s["unanswered_count"] == 2  # 1 نزده + 1 ثبت‌نشده
    assert s["percent_konkur"] == 40.1      # (5 − 0.33×3)/10 × 100
    assert s["percent_no_penalty"] == 50.0  # 5/10 × 100
    assert s["penalty_k"] == 0.33


def test_finish_negative_percent_is_shown(client):
    """show_negative=true — درصد منفی نمایش داده می‌شود (doc 08 §8.1)."""
    u, rid, topic = _setup(client, "f2@example.com")
    data = _create(client, u, rid, from_number=1, to_number=5)
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}
    items = [{"question_id": qid, "status": "answered", "result": "wrong"} for qid in qs.values()]
    client.post(f"/api/v1/test-sessions/{sid}/records", json={"items": items}, headers=_h(u))
    s = client.post(f"/api/v1/test-sessions/{sid}/finish", json={}, headers=_h(u)).json()["data"]["session"]
    assert s["percent_konkur"] == -33.0  # (0 − 0.33×5)/5 × 100
    assert s["percent_no_penalty"] == 0.0


def test_finish_idempotent_and_locks_records_v2_t02(client):
    from app.core.events import TEST_RECORDS_CREATED, event_bus

    u, rid, topic = _setup(client, "f3@example.com")
    data = _create(client, u, rid, from_number=1, to_number=4)
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}
    client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [{"question_id": qs[1], "status": "answered", "result": "correct"}]},
        headers=_h(u),
    )

    events: list = []
    handler = events.append
    event_bus.subscribe(TEST_RECORDS_CREATED, handler)
    try:
        f1 = client.post(f"/api/v1/test-sessions/{sid}/finish", json={"actual_duration": 900}, headers=_h(u))
        f2 = client.post(f"/api/v1/test-sessions/{sid}/finish", json={"actual_duration": 1}, headers=_h(u))
    finally:
        event_bus.unsubscribe(TEST_RECORDS_CREATED, handler)

    assert f1.status_code == 200 and f2.status_code == 200
    d1, d2 = f1.json()["data"], f2.json()["data"]
    assert d1["idempotent"] is False
    assert d2["idempotent"] is True
    assert d1["session"]["finished_at"] == d2["session"]["finished_at"]  # بدون تغییر
    assert d1["session"]["actual_duration"] == 900
    assert d2["session"]["actual_duration"] == 900  # مقدار اول حفظ شد
    finish_events = [e for e in events if e.payload.get("finished")]
    assert len(finish_events) == 1  # رویداد finish فقط یک‌بار

    # records بعد از finish → 409 (تاریخچه قفل است)
    locked = client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [{"question_id": qs[2], "status": "answered", "result": "correct"}]},
        headers=_h(u),
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["message"] == "جلسه پایان یافته است؛ تاریخچه نتایج قفل است (append-only)."


# --- past import ------------------------------------------------------------------------

def test_past_import_not_entered_then_completion_v2_t03(client):
    u, rid, topic = _setup(client, "p1@example.com")

    r = client.post(
        "/api/v1/tests/past-import",
        json={
            "resource_id": rid,
            "topic_id": topic["id"],
            "label": "کنکور ۱۴۰۲",
            "items": [
                {"number": 1, "status": "answered", "answer": "2"},   # کلید 1%4+1=2 → correct
                {"number": 2, "status": "answered", "answer": "1"},   # کلید 3 → wrong
                {"number": 3, "status": "not_entered"},
                {"number": 4, "status": "unanswered"},
            ],
        },
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert data["created_session"] is True
    assert data["imported"] == 4
    s = data["session"]
    assert s["mode"] == "past"
    assert s["not_entered_count"] == 1
    assert s["correct_count"] == 1 and s["wrong_count"] == 1 and s["unanswered_count"] == 1
    assert s["total_count"] == 4
    assert s["percent_konkur"] == round((1 - 0.33 * 1) / 4 * 100, 2)  # 16.75
    assert s["percent_konkur"] == 16.75

    # تکمیل بعدی: not_entered → answered (همان attempt، نه duplicate) — doc 09 §9.3
    r2 = client.post(
        "/api/v1/tests/past-import",
        json={
            "resource_id": rid,
            "topic_id": topic["id"],
            "label": "کنکور ۱۴۰۲",
            "items": [{"number": 3, "status": "answered", "answer": "4"}],  # کلید 3%4+1=4 → correct
        },
        headers=_h(u),
    )
    assert r2.status_code == 200, r2.text
    d2 = r2.json()["data"]
    assert d2["created_session"] is False  # همان جلسه قبلی
    assert d2["imported"] == 0 and d2["updated"] == 1
    s2 = d2["session"]
    assert s2["id"] == s["id"]
    assert s2["total_count"] == 4  # duplicate ساخته نشد
    assert s2["not_entered_count"] == 0
    assert s2["correct_count"] == 2 and s2["wrong_count"] == 1
    assert s2["percent_konkur"] == round((2 - 0.33 * 1) / 4 * 100, 2)  # 41.75

    detail = client.get(f"/api/v1/test-sessions/{s['id']}", headers=_h(u)).json()["data"]
    q3 = [a for a in detail["attempts"] if a["question_number"] == 3]
    assert len(q3) == 1  # همان attempt تبدیل شد
    assert q3[0]["status"] == "answered" and q3[0]["result"] == "correct"


def test_past_import_creates_missing_questions_and_keys(client):
    """کتاب TOC-only + past import → سوال و کلید نسخه‌دار ساخته می‌شود."""
    toc_only = {"title": "فیزیک پایه", "chapters": [{"title": "فصل ۱", "topics": [{"title": "حرکت"}]}]}
    u, rid, topic = _setup(client, "p2@example.com", book=toc_only)

    r = client.post(
        "/api/v1/tests/past-import",
        json={
            "resource_id": rid,
            "topic_id": topic["id"],
            "label": "آزمون ۱",
            "items": [
                {"number": 1, "status": "answered", "answer": "3", "correct_answer": "3"},
                {"number": 2, "status": "answered", "answer": "1", "correct_answer": "4"},
            ],
        },
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    d = r.json()["data"]
    assert d["created_questions"] == 2
    assert d["created_answer_keys"] == 2
    assert d["session"]["correct_count"] == 1
    assert d["session"]["wrong_count"] == 1

    # سوال‌ها حالا در درخت کتاب دیده می‌شوند
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    assert tree[0]["children"][0]["question_count"] == 2

    # کلید جدید برای سوال ۱ → نسخه ۲ (append-only keys)
    r2 = client.post(
        "/api/v1/tests/past-import",
        json={
            "resource_id": rid,
            "topic_id": topic["id"],
            "label": "آزمون ۱",
            "items": [{"number": 1, "status": "answered", "answer": "2", "correct_answer": "2"}],
        },
        headers=_h(u),
    )
    assert r2.status_code == 200
    assert r2.json()["data"]["created_answer_keys"] == 1
    detail = client.get(f"/api/v1/test-sessions/{r2.json()['data']['session']['id']}", headers=_h(u)).json()["data"]
    q1 = [a for a in detail["attempts"] if a["question_number"] == 1][-1]
    assert q1["answer_key_version"] == 2
    assert q1["result"] == "correct"  # answer=2 با کلید نسخه ۲


# --- error notebook ------------------------------------------------------------------------

def test_error_notebook_auto_and_update(client):
    u, rid, topic = _setup(client, "e1@example.com")
    data = _create(client, u, rid, from_number=1, to_number=3)
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}
    client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [
            {"question_id": qs[1], "status": "answered", "result": "wrong", "answer": "3"},
            {"question_id": qs[2], "status": "answered", "result": "correct"},
        ]},
        headers=_h(u),
    )

    r = client.get("/api/v1/tests/error-notebook", headers=_h(u))
    assert r.status_code == 200
    items = r.json()["data"]["items"]
    assert len(items) == 1  # فقط غلط‌ها
    note = items[0]
    assert note["question_number"] == 1
    assert note["book_title"] == "ریاضی جامع"
    assert note["topic_title"] == "تابع"
    assert note["your_answer"] == "3"
    assert note["correct_answer"] == "2"
    assert note["error_type"] is None

    up = client.put(
        f"/api/v1/tests/error-notebook/{note['id']}",
        json={"error_type": "careless", "note": "عجله در خواندن صورت سوال"},
        headers=_h(u),
    )
    assert up.status_code == 200, up.text
    d = up.json()["data"]
    assert d["error_type"] == "careless"
    assert d["error_type_fa"] == "بی‌دقتی"
    assert d["note"] == "عجله در خواندن صورت سوال"

    # تکرار غلط روی همان attempt → یادداشت duplicate ساخته نمی‌شود
    r2 = client.get("/api/v1/tests/error-notebook", headers=_h(u))
    assert len(r2.json()["data"]["items"]) == 1


# --- time tracking + history + auth ----------------------------------------------------------

def test_time_tracking_per_attempt_and_aggregate(client):
    u, rid, topic = _setup(client, "t1@example.com")
    data = _create(client, u, rid, from_number=1, to_number=3)
    sid = data["session"]["id"]
    qs = {q["number"]: q["question_id"] for q in data["questions"]}
    client.post(
        f"/api/v1/test-sessions/{sid}/records",
        json={"items": [
            {"question_id": qs[1], "status": "answered", "result": "correct", "duration_seconds": 60},
            {"question_id": qs[2], "status": "answered", "result": "wrong", "duration_seconds": 120},
        ]},
        headers=_h(u),
    )
    fin = client.post(f"/api/v1/test-sessions/{sid}/finish", json={}, headers=_h(u)).json()["data"]
    assert fin["session"]["actual_duration"] == 180  # از timer هر attempt (doc 09 §9.4)
    agg = fin["topics"][0]
    assert agg["topic_title"] == "تابع"
    assert agg["duration_seconds"] == 180
    assert agg["attempts"] == 2
    assert agg["correct"] == 1 and agg["wrong"] == 1
    assert agg["avg_seconds"] == 90.0

    # untimed: مدت کل را UI بعد از finish می‌پرسد
    data2 = _create(client, u, rid, from_number=4, to_number=5)
    sid2 = data2["session"]["id"]
    fin2 = client.post(f"/api/v1/test-sessions/{sid2}/finish", json={"actual_duration": 420}, headers=_h(u)).json()["data"]
    assert fin2["session"]["actual_duration"] == 420


def test_sessions_history_list(client):
    u, rid, topic = _setup(client, "t2@example.com")
    d1 = _create(client, u, rid, from_number=1, to_number=2)
    _create(client, u, rid, from_number=3, to_number=4)
    client.post(
        f"/api/v1/test-sessions/{d1['session']['id']}/records",
        json={"items": [{"number": 1, "status": "answered", "result": "correct"}]},
        headers=_h(u),
    )
    r = client.get("/api/v1/test-sessions", headers=_h(u))
    items = r.json()["data"]["items"]
    assert len(items) == 2
    assert items[0]["resource_title"] == "ریاضی جامع"
    assert any(s["id"] == d1["session"]["id"] for s in items)


def test_engine_auth_required(client):
    for path in ("/api/v1/test-sessions", "/api/v1/tests/error-notebook"):
        r = client.get(path)
        assert r.status_code == 401
        assert r.json()["error"]["message"] == "برای ادامه باید وارد شوید."
    r = client.post("/api/v1/tests/past-import", json={})
    assert r.status_code == 401


def test_session_not_found_persian(client):
    u, rid, topic = _setup(client, "t3@example.com")
    r = client.get("/api/v1/test-sessions/nope", headers=_h(u))
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "جلسه پیدا نشد."
