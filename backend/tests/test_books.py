"""Phase 2 — Book Engine, TOC-only import (doc 08 §8.3, doc 09 §9.1, doc 06 §Books).

پذیرش اجباری فاز ۲:
- import فایل فقط‌فهرست بدون هیچ question موفق شود
- خطای «باید حداقل یک سوال داشته باشد» دیگر وجود نداشته باشد
"""
from __future__ import annotations

PASS = "pass1234"

FORBIDDEN_MSG = "باید حداقل یک سوال داشته باشد"


def _user(client, email: str) -> dict:
    r = client.post("/api/v1/auth/register", json={"email": email, "password": PASS})
    assert r.status_code == 200, r.text
    return {"token": r.json()["data"]["access_token"]}


def _h(u):
    return {"Authorization": f"Bearer {u['token']}"}


# doc 09 §9.1 حالت A — TOC-only، بدون هیچ سوالی
TOC_ONLY = {
    "title": "شیمی ۲",
    "publisher": "مبتکران",
    "subject": "شیمی",
    "chapters": [
        {
            "title": "فصل ۱",
            "topics": [
                {
                    "title": "الگوها و روندها",
                    "block_type": "topic",
                    "subtopics": [{"title": "جدول دوره‌ای"}],
                }
            ],
        }
    ],
}


def _import(client, u, payload):
    return client.post("/api/v1/resources/import-book", json=payload, headers=_h(u))


# --- پذیرش اجباری: TOC-only ---------------------------------------------------

def test_import_toc_only_without_any_question_succeeds(client):
    u = _user(client, "toc1@example.com")
    r = _import(client, u, TOC_ONLY)
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True
    data = r.json()["data"]
    assert data["resource"]["title"] == "شیمی ۲"
    assert data["resource"]["publisher"] == "مبتکران"
    counts = data["resource"]["counts"]
    assert counts["chapters"] == 1
    assert counts["topics"] == 2  # الگوها + جدول دوره‌ای
    assert counts["questions"] == 0
    # پذیرش اجباری: این خطا هرگز نباید وجود داشته باشد
    assert FORBIDDEN_MSG not in r.text


def test_import_questions_absent_and_empty_both_ok(client):
    u = _user(client, "toc2@example.com")
    absent = {"title": "فیزیک ۱", "chapters": [{"title": "فصل ۱", "topics": [{"title": "اندازه‌گیری"}]}]}
    r1 = _import(client, u, absent)
    assert r1.status_code == 200, r1.text
    assert FORBIDDEN_MSG not in r1.text

    empty = {
        "title": "فیزیک ۲",
        "chapters": [{"title": "فصل ۱", "topics": [{"title": "کار و انرژی", "questions": []}]}],
    }
    r2 = _import(client, u, empty)
    assert r2.status_code == 200, r2.text
    assert r2.json()["data"]["resource"]["counts"]["questions"] == 0
    assert FORBIDDEN_MSG not in r2.text


def test_topic_without_direct_questions_only_subtopics_ok(client):
    u = _user(client, "toc3@example.com")
    payload = {
        "title": "ریاضی پایه",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {
                        "title": "مجموعه‌ها",
                        "subtopics": [{"title": "زیرمجموعه"}, {"title": "اجتماع و اشتراک"}],
                    }
                ],
            }
        ],
    }
    r = _import(client, u, payload)
    assert r.status_code == 200, r.text
    assert FORBIDDEN_MSG not in r.text
    tree = client.get(f"/api/v1/resources/{r.json()['data']['resource']['id']}/tree", headers=_h(u))
    node = tree.json()["data"]["tree"][0]["children"][0]
    assert node["question_count"] == 0
    assert len(node["children"]) == 2


# --- block_type ----------------------------------------------------------------

def test_block_type_inference_from_title(client):
    u = _user(client, "bt1@example.com")
    payload = {
        "title": "کتاب تست",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {"title": "مرور مبحث"},                 # → topic
                    {"title": "کنکور ۱۴۰۳"},                # → konkur
                    {"title": "آزمون فصل ۲"},               # → chapter_exam
                    {"title": "آزمون جامع"},                # → chapter_exam
                    {"title": "[آزمون]"},                   # → chapter_exam (doc 08 §8.3.4)
                    {"title": "چکاپ فصل"},                  # → checkup
                    {"title": "سوالات مخلوط"},              # → mixed
                    {"title": "پیوست", "block_type": "other"},  # صریح → other
                    {"title": "کنکور", "block_type": "topic"},  # صریح بر استنتاج غلبه می‌کند
                ],
            }
        ],
    }
    r = _import(client, u, payload)
    assert r.status_code == 200, r.text
    tree = client.get(f"/api/v1/resources/{r.json()['data']['resource']['id']}/tree", headers=_h(u))
    types = [c["block_type"] for c in tree.json()["data"]["tree"][0]["children"]]
    assert types == [
        "topic", "konkur", "chapter_exam", "chapter_exam",
        "chapter_exam", "checkup", "mixed", "other", "topic",
    ]


def test_block_type_enum_rejects_invalid(client):
    u = _user(client, "bt2@example.com")
    payload = {"title": "کتاب", "chapters": [{"title": "فصل", "topics": [{"title": "م", "block_type": "quiz"}]}]}
    r = _import(client, u, payload)
    assert r.status_code == 422
    body = r.json()
    assert body["success"] is False
    assert body["error"]["message"]  # Persian message exists


# --- duplicate → 409 -------------------------------------------------------------

def test_duplicate_title_publisher_409_and_replace_option(client):
    u = _user(client, "dup1@example.com")
    r1 = _import(client, u, TOC_ONLY)
    assert r1.status_code == 200

    r2 = _import(client, u, TOC_ONLY)
    assert r2.status_code == 409
    body = r2.json()
    assert body["success"] is False
    assert body["error"]["code"] == "CONFLICT"
    assert "قبلاً وارد شده" in body["error"]["message"]
    assert FORBIDDEN_MSG not in r2.text

    # گزینه به‌روزرسانی (doc 08 §8.3.5): replace=true → جایگزینی، نه duplicate
    r3 = _import(client, u, {**TOC_ONLY, "replace": True})
    assert r3.status_code == 200
    assert r3.json()["data"]["replaced"] is True

    listing = client.get("/api/v1/resources", headers=_h(u)).json()["data"]["items"]
    same = [b for b in listing if b["title"] == "شیمی ۲" and b["publisher"] == "مبتکران"]
    assert len(same) == 1


def test_same_title_different_publisher_ok(client):
    u = _user(client, "dup2@example.com")
    assert _import(client, u, TOC_ONLY).status_code == 200
    r = _import(client, u, {**TOC_ONLY, "publisher": "گاج"})
    assert r.status_code == 200, r.text


def test_missing_publisher_duplicate_detected(client):
    u = _user(client, "dup3@example.com")
    payload = {"title": "بدون ناشر", "chapters": []}
    assert _import(client, u, payload).status_code == 200
    r = _import(client, u, payload)
    assert r.status_code == 409  # publisher غایب هم یکتایی را نقض می‌کند


# --- tree / list / schema ---------------------------------------------------------

def test_resources_list_and_tree_shapes(client):
    u = _user(client, "tree1@example.com")
    rid = _import(client, u, TOC_ONLY).json()["data"]["resource"]["id"]

    listing = client.get("/api/v1/resources", headers=_h(u))
    assert listing.status_code == 200
    items = listing.json()["data"]["items"]
    assert any(b["id"] == rid for b in items)

    r = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["resource"]["id"] == rid
    chapter = data["tree"][0]
    assert chapter["title"] == "فصل ۱"
    assert chapter["is_structural"] is True
    topic = chapter["children"][0]
    assert topic["block_type"] == "topic"
    assert topic["block_type_fa"] == "مبحث"
    assert topic["taught"] is False
    assert topic["taught_state"] == "none"
    sub = topic["children"][0]
    assert sub["title"] == "جدول دوره‌ای"  # نیم‌فاصله دست‌نخورده می‌ماند
    assert sub["is_structural"] is False


def test_tree_404_persian(client):
    u = _user(client, "tree2@example.com")
    r = client.get("/api/v1/resources/not-exists/tree", headers=_h(u))
    assert r.status_code == 404
    assert r.json()["error"]["message"] == "کتاب پیدا نشد."


def test_import_schema_endpoint(client):
    u = _user(client, "schema1@example.com")
    r = client.get("/api/v1/resources/import-book/schema", headers=_h(u))
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["toc_only"] is True
    assert data["example"]["title"] == "شیمی ۲"
    assert {b["value"] for b in data["block_types"]} == {
        "topic", "mixed", "chapter_exam", "checkup", "konkur", "other",
    }
    assert any("number" in rule or "answer" in rule for rule in data["rules"])


# --- questions mode B (doc 09 §9.1) --------------------------------------------------

def test_questions_import_when_present(client):
    u = _user(client, "q1@example.com")
    payload = {
        "title": "زیست ۱",
        "chapters": [
            {
                "title": "فصل ۱",
                "topics": [
                    {
                        "title": "گوارش",
                        "questions": [
                            {"number": 1, "answer": "2", "difficulty": 3, "tags": ["سخت"]},
                            {"number": 2, "answer": "4"},
                        ],
                    }
                ],
            }
        ],
    }
    r = _import(client, u, payload)
    assert r.status_code == 200, r.text
    counts = r.json()["data"]["resource"]["counts"]
    assert counts["questions"] == 2

    tree = client.get(f"/api/v1/resources/{r.json()['data']['resource']['id']}/tree", headers=_h(u))
    topic = tree.json()["data"]["tree"][0]["children"][0]
    assert topic["question_count"] == 2


def test_question_requires_number_and_answer(client):
    u = _user(client, "q2@example.com")
    no_answer = {"title": "ک", "chapters": [{"title": "ف", "topics": [{"title": "م", "questions": [{"number": 1}]}]}]}
    r = _import(client, u, no_answer)
    assert r.status_code == 422
    assert "پاسخ" in r.json()["error"]["message"]

    no_number = {"title": "ک", "chapters": [{"title": "ف", "topics": [{"title": "م", "questions": [{"answer": "2"}]}]}]}
    r = _import(client, u, no_number)
    assert r.status_code == 422
    assert "شماره" in r.json()["error"]["message"]


def test_book_title_required(client):
    u = _user(client, "q3@example.com")
    r = _import(client, u, {"chapters": []})
    assert r.status_code == 422
    assert r.json()["error"]["message"] == "عنوان کتاب الزامی است."


# --- auth -------------------------------------------------------------------------

def test_resources_require_auth(client):
    r = client.get("/api/v1/resources")
    assert r.status_code == 401
    assert r.json()["error"]["message"] == "برای ادامه باید وارد شوید."

    r2 = client.post("/api/v1/resources/import-book", json=TOC_ONLY)
    assert r2.status_code == 401


# --- taught cascade با درخت واقعی (doc 08 §8.8) ---------------------------------------

def test_taught_cascade_with_real_book_tree(client):
    u = _user(client, "casc1@example.com")
    rid = _import(client, u, TOC_ONLY).json()["data"]["resource"]["id"]
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    chapter = tree[0]
    topic = chapter["children"][0]
    subtopic = topic["children"][0]

    # parent (topic) taught=True → child (subtopic) هم cascade می‌شود
    r = client.put(
        "/api/v1/students/me/taught-topics",
        json={"items": [{"topic_id": topic["id"], "taught": True}]},
        headers=_h(u),
    )
    assert r.status_code == 200, r.text
    items = {i["topic_id"]: i["taught"] for i in r.json()["data"]["items"]}
    assert items[topic["id"]] is True
    assert items[subtopic["id"]] is True          # cascade parent→child
    assert chapter["id"] not in items             # parent بالاتر دست‌نخورده

    tree2 = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    ch = tree2[0]
    assert ch["taught"] is False
    assert ch["taught_state"] == "partial"        # doc 08 §8.8 — indeterminate
    assert ch["children"][0]["taught_state"] == "all"

    # taught=False روی parent هیچ نواده‌ای را برنمی‌گرداند
    r2 = client.put(
        "/api/v1/students/me/taught-topics",
        json={"items": [{"topic_id": topic["id"], "taught": False}]},
        headers=_h(u),
    )
    items2 = {i["topic_id"]: i["taught"] for i in r2.json()["data"]["items"]}
    assert items2[topic["id"]] is False
    assert items2[subtopic["id"]] is True


def test_replace_book_clears_old_taught_rows(client):
    u = _user(client, "casc2@example.com")
    rid = _import(client, u, TOC_ONLY).json()["data"]["resource"]["id"]
    tree = client.get(f"/api/v1/resources/{rid}/tree", headers=_h(u)).json()["data"]["tree"]
    topic_id = tree[0]["children"][0]["id"]
    client.put(
        "/api/v1/students/me/taught-topics",
        json={"items": [{"topic_id": topic_id, "taught": True}]},
        headers=_h(u),
    )

    r = _import(client, u, {**TOC_ONLY, "replace": True})
    assert r.status_code == 200
    new_rid = r.json()["data"]["resource"]["id"]

    taught = client.get("/api/v1/students/me/taught-topics", headers=_h(u)).json()["data"]["items"]
    assert topic_id not in {t["topic_id"] for t in taught}  # ردیف‌های کتاب قدیمی پاک شدند

    tree2 = client.get(f"/api/v1/resources/{new_rid}/tree", headers=_h(u)).json()["data"]["tree"]
    assert tree2[0]["children"][0]["taught"] is False
