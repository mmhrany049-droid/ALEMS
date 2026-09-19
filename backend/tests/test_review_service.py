"""تست‌های سرویس مرور — چرخه ۱→۳→۷→۱۴، بازگشت سررسید، postpone و رویداد تیک‌ها.

این تست‌ها رفتار سطح سرویس (با دیتابیس واقعی جلسه تست) را برای قوانین سند 08 §8.2
ثبت می‌کنند؛ تست‌های خالص دامنه در test_domain_review.py هستند.
"""
from __future__ import annotations

import copy
import datetime as dt
import uuid

import pytest


def _uname() -> str:
    return f"rv_{uuid.uuid4().hex[:8]}"


SMALL_BOOK = {
    "title": "کتاب مرور",
    "publisher": "نشر تست",
    "chapters": [{"title": "ف۱", "topics": [{
        "title": "م۱",
        "questions": [
            {"number": str(i), "answer": "2", "difficulty": "متوسط"}
            for i in range(1, 6)
        ],
    }]}],
}


@pytest.fixture()
def review_env(client):
    """کاربر + کتاب ۵ سوالی + ثبت ۲ غلط و ۱ درست؛ خروجی: client و داده‌ها."""
    uname = _uname()
    client.post("/api/v1/auth/register", json={"username": uname, "password": "secret123"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": "secret123"})
    client.headers.update({"Authorization": f"Bearer {r.json()['data']['access_token']}"})

    book = copy.deepcopy(SMALL_BOOK)
    book["title"] += f" — {uuid.uuid4().hex[:6]}"
    rid = client.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
    questions = client.get(f"/api/v1/resources/{rid}/questions").json()["data"]

    client.post("/api/v1/test-records", json={"records": [
        {"question_id": questions[0]["id"], "result": "wrong", "error_type": "careless"},
        {"question_id": questions[1]["id"], "result": "wrong", "error_type": "forgotten"},
        {"question_id": questions[2]["id"], "result": "correct"},
    ]})
    queue = client.get("/api/v1/reviews/queue").json()["data"]
    assert len(queue) == 2  # فقط غلط‌ها
    return {
        "client": client,
        "questions": questions,
        "queue": queue,
        "wrong_items": [i for i in queue if i["reason"] == "wrong"],
    }


class TestSpacedRepetitionCycle:
    """چرخه ۱ → ۳ → ۷ → ۱۴ — دقیقاً طبق قانون ۸.۲ بند ۶."""

    @staticmethod
    def _make_due(client, item_id: str) -> None:
        """شبیه‌سازی گذر زمان: تاریخ مرور بعدی را به دیروز ببر."""
        from app.db.session import SessionLocal
        from app.modules.activity.models import ReviewItem

        db = SessionLocal()
        try:
            row = db.get(ReviewItem, uuid.UUID(item_id))
            row.scheduled_date = dt.date.today() - dt.timedelta(days=1)
            db.commit()
        finally:
            db.close()

    def test_four_completions_use_1_3_7_14(self, review_env):
        """پس از مرور اول +۱، دوم +۳، سوم +۷، چهارم +۱۴ روز."""
        client = review_env["client"]
        item = review_env["queue"][0]
        today = dt.date.today()
        expected = [1, 3, 7, 14]

        for nth, gap in enumerate(expected, start=1):
            r = client.post(f"/api/v1/reviews/{item['id']}/complete")
            assert r.status_code == 200, r.text
            data = r.json()["data"]
            assert data["status"] == "done"
            next_date = dt.date.fromisoformat(data["scheduled_date"])
            assert next_date == today + dt.timedelta(days=gap), (
                f"مرور شماره {nth}: انتظار +{gap} روز"
            )
            assert data["review_count"] == nth

            # سررسید می‌رسد → بازسازی → آیتم برمی‌گردد (تا وقتی چرخه تمام نشده)
            self._make_due(client, item["id"])
            client.post("/api/v1/reviews/rebuild")
            q = client.get("/api/v1/reviews/queue").json()["data"]
            ids = [i["id"] for i in q]
            if nth < len(expected):
                assert item["id"] in ids, f"پس از مرور {nth}، آیتم باید در سررسید بعدی برگردد"

        # بعد از چهار مرور، چرخه کامل است — دیگر برنمی‌گردد
        client.post("/api/v1/reviews/rebuild")
        q = client.get("/api/v1/reviews/queue").json()["data"]
        assert item["id"] not in [i["id"] for i in q]

    def test_done_not_due_stays_out_of_queue(self, review_env):
        """آیتم مرور‌شده که سررسیدش نرسیده، در صف نیست."""
        client = review_env["client"]
        item = review_env["queue"][0]
        client.post(f"/api/v1/reviews/{item['id']}/complete")
        # بدون جلو زدن تاریخ — بازسازی
        client.post("/api/v1/reviews/rebuild")
        q = client.get("/api/v1/reviews/queue").json()["data"]
        assert item["id"] not in [i["id"] for i in q]

    def test_reenter_preserves_review_count(self, review_env):
        """آیتم بازگشتی، شمارنده مرورهای قبلی را نگه می‌دارد (چرخه ادامه می‌یابد)."""
        client = review_env["client"]
        item = review_env["queue"][0]
        r = client.post(f"/api/v1/reviews/{item['id']}/complete").json()["data"]
        assert r["review_count"] == 1
        # جلو زدن زمان: بازسازی پس از سررسید (+۱ روز)
        from app.core.config import settings
        from app.db.session import SessionLocal
        from app.modules.activity.models import ReviewItem

        db = SessionLocal()
        try:
            row = db.get(ReviewItem, uuid.UUID(item["id"]))
            row.scheduled_date = dt.date.today() - dt.timedelta(days=1)  # سررسید گذشته
            db.commit()
        finally:
            db.close()

        client.post("/api/v1/reviews/rebuild")
        q = client.get("/api/v1/reviews/queue").json()["data"]
        me = next(i for i in q if i["id"] == item["id"])
        assert me["status"] == "pending"
        assert me["review_count"] == 1  # حفظ شده
        # مرور دوم → +۳ روز
        r = client.post(f"/api/v1/reviews/{item['id']}/complete").json()["data"]
        assert dt.date.fromisoformat(r["scheduled_date"]) == dt.date.today() + dt.timedelta(days=3)


class TestQueueRules:
    """قوانین ساخت صف (۸.۲)."""

    def test_rebuild_stats(self, review_env):
        client = review_env["client"]
        r = client.post("/api/v1/reviews/rebuild").json()["data"]
        assert set(r.keys()) == {"added", "removed", "reentered", "pending"}
        assert r["added"] == 0  # صف از قبل بر اساس رویداد ساخته شده
        assert r["pending"] == 2

    def test_mark_add_enters_queue_via_event(self, review_env):
        """تیک مهم روی سوال درست → خودکار وارد صف می‌شود (رویداد question_marks.changed)."""
        client = review_env["client"]
        correct_q = review_env["questions"][2]  # قبلاً درست answered شده
        r = client.post(f"/api/v1/questions/{correct_q['id']}/marks",
                        json={"mark_type": "important"})
        assert r.status_code == 200
        q = client.get("/api/v1/reviews/queue").json()["data"]
        ids = {i["question_id"] for i in q}
        assert correct_q["id"] in ids  # با تیک مهم وارد صف شد
        item = next(i for i in q if i["question_id"] == correct_q["id"])
        assert item["reason"] == "mark_important"

    def test_mark_remove_leaves_queue_on_rebuild(self, review_env):
        """حذف تیک → با بازسازی بعدی از صف خارج می‌شود."""
        client = review_env["client"]
        correct_q = review_env["questions"][2]
        client.post(f"/api/v1/questions/{correct_q['id']}/marks",
                    json={"mark_type": "important"})
        client.delete(f"/api/v1/questions/{correct_q['id']}/marks/important")
        client.post("/api/v1/reviews/rebuild")
        q = client.get("/api/v1/reviews/queue").json()["data"]
        assert correct_q["id"] not in {i["question_id"] for i in q}

    def test_multiple_marks_keep_question(self, review_env):
        """تیک mistake/tip وارد صف نمی‌شوند ولی مهم/سخت/مرور می‌شوند."""
        client = review_env["client"]
        q1 = review_env["questions"][3]  # هنوز answered نشده
        client.post(f"/api/v1/questions/{q1['id']}/marks", json={"mark_type": "tip"})
        client.post(f"/api/v1/questions/{q1['id']}/marks", json={"mark_type": "mistake"})
        q = client.get("/api/v1/reviews/queue").json()["data"]
        assert q1["id"] not in {i["question_id"] for i in q}
        # تیک سخت → وارد صف
        client.post(f"/api/v1/questions/{q1['id']}/marks", json={"mark_type": "hard"})
        q = client.get("/api/v1/reviews/queue").json()["data"]
        assert q1["id"] in {i["question_id"] for i in q}


class TestPostpone:
    """«بعداً» — به‌عقب‌انداختن (سند 07 §7.4)."""

    def test_postpone_moves_date_keeps_pending(self, review_env):
        client = review_env["client"]
        item = review_env["queue"][0]
        r = client.post(f"/api/v1/reviews/{item['id']}/postpone", json={"days": 2})
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["status"] == "pending"
        assert data["scheduled_date"] == (
            dt.date.today() + dt.timedelta(days=2)).isoformat()

    def test_postpone_default_one_day(self, review_env):
        client = review_env["client"]
        item = review_env["queue"][0]
        r = client.post(f"/api/v1/reviews/{item['id']}/postpone")
        assert r.json()["data"]["scheduled_date"] == (
            dt.date.today() + dt.timedelta(days=1)).isoformat()

    def test_postpone_rejects_done(self, review_env):
        client = review_env["client"]
        item = review_env["queue"][0]
        client.post(f"/api/v1/reviews/{item['id']}/complete")
        r = client.post(f"/api/v1/reviews/{item['id']}/postpone")
        assert r.status_code == 422

    def test_invalid_days_rejected(self, review_env):
        client = review_env["client"]
        item = review_env["queue"][0]
        r = client.post(f"/api/v1/reviews/{item['id']}/postpone", json={"days": 99})
        assert r.status_code == 422


class TestErrorNotebookRules:
    """دفترچه خطا — قانون ۸.۳: error_type فقط برای wrong."""

    def test_all_four_error_types_persist(self, review_env):
        client = review_env["client"]
        qs = review_env["questions"]
        client.post("/api/v1/test-records", json={"records": [
            {"question_id": qs[0]["id"], "result": "wrong", "error_type": "unknown"},
            {"question_id": qs[1]["id"], "result": "wrong", "error_type": "forgotten"},
        ]})
        r = client.get("/api/v1/test-records")
        types = {x["error_type"] for x in r.json()["data"] if x["result"] == "wrong"}
        assert {"careless", "forgotten", "unknown"} <= types

    def test_mistake_types_analytics_counts(self, review_env):
        client = review_env["client"]
        r = client.get("/api/v1/analytics/mistake-types")
        types = {t["error_type"] for t in r.json()["data"]}
        assert "careless" in types and "forgotten" in types
