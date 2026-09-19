"""تست‌های پذیرش نسخه ۱ — AT-01 تا AT-27 (طبق 10_ACCEPTANCE_TESTS.md)."""
from __future__ import annotations

import datetime as dt
import copy
import uuid

import pytest


def _h(client) -> dict:
    return {"Authorization": f"Bearer {client.headers.get('Authorization', '').replace('Bearer ', '')}"} \
        if client.headers.get("Authorization") else {}


# ============ ۱۰.۱ Foundation و هویت ============

class TestFoundationIdentity:
    def test_at_01_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_at_02_register_and_login(self, client):
        r = client.post("/api/v1/auth/register", json={
            "username": "at02_user", "password": "secret123"})
        assert r.status_code == 200
        assert r.json()["data"]["username"] == "at02_user"
        r = client.post("/api/v1/auth/login", json={
            "username": "at02_user", "password": "secret123"})
        assert r.status_code == 200
        assert r.json()["data"]["access_token"]
        # اطلاعات کاربر جاری
        token = r.json()["data"]["access_token"]
        r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.json()["data"]["username"] == "at02_user"

    def test_at_03_wrong_password_persian_error(self, client):
        client.post("/api/v1/auth/register", json={
            "username": "at03_user", "password": "secret123"})
        r = client.post("/api/v1/auth/login", json={
            "username": "at03_user", "password": "wrong-pass"})
        assert r.status_code == 401
        body = r.json()
        assert body["success"] is False
        assert body["error"]["message"]  # پیام فارسی خوانا
        assert any("\u0600" <= ch <= "\u06FF" for ch in body["error"]["message"]), \
            "پیام خطا باید فارسی باشد"

    def test_at_04_complete_profile(self, auth_client):
        r = auth_client.get("/api/v1/students/me")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["grade"] == "دوازدهم"
        assert data["field"] == "ریاضی"
        assert data["target_rank"] == 100
        assert data["is_complete"] is True

    def test_at_05_daily_state(self, auth_client):
        today = dt.date.today().isoformat()
        r = auth_client.post("/api/v1/students/me/state", json={
            "date": today, "energy_level": 4, "mood": "خوب", "study_condition": "متمرکز",
        })
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["energy_level"] == 4
        # خواندن بازه
        r = auth_client.get(f"/api/v1/students/me/state?from={today}&to={today}")
        assert len(r.json()["data"]) == 1
        # انرژی نامعتبر رد می‌شود
        r = auth_client.post("/api/v1/students/me/state", json={"energy_level": 9})
        assert r.status_code == 422


# ============ ۱۰.۲ دانش آموزشی ============

SAMPLE_BOOK = {
    "title": "کتاب تست حد و مشتق",
    "publisher": "انتشارات تست",
    "subject": "حسابان",
    "chapters": [
        {"title": "فصل تابع", "topics": [
            {"title": "تعریف تابع", "questions": [
                {"number": "1", "answer": "1", "difficulty": "easy", "importance": 2},
                {"number": "2", "answer": "3", "difficulty": "medium"},
                {"number": "3", "answer": "2", "difficulty": "hard", "tags": ["تابع"]},
            ]},
            {"title": "دامنه تابع", "questions": [
                {"number": "1", "answer": "4", "difficulty": "medium"},
                {"number": "2", "answer": "1", "difficulty": "easy"},
            ]},
        ]},
        {"title": "فصل حد", "topics": [
            {"title": "حد در بی‌نهایت", "questions": [
                {"number": "1", "answer": "2", "difficulty": "hard"},
                {"number": "2", "answer": "3", "difficulty": "medium"},
                {"number": "3", "answer": "1", "difficulty": "easy"},
            ]},
        ]},
    ],
}


def _import_sample_book(auth_client, book: dict | None = None) -> dict:
    payload = copy.deepcopy(book or SAMPLE_BOOK)
    if book is None:
        # هر تست کتاب مستقل خودش را دارد (دیتابیس جلسه تست مشترک است)
        suffix = uuid.uuid4().hex[:6]
        payload["title"] = f"{payload['title']} — {suffix}"
        payload["publisher"] = f"{payload['publisher']} — {suffix}"
    r = auth_client.post("/api/v1/resources/import-book", json=payload)
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _get_questions(auth_client, resource_id: str) -> list[dict]:
    r = auth_client.get(f"/api/v1/resources/{resource_id}/questions?page_size=100")
    assert r.status_code == 200
    return r.json()["data"]


class TestKnowledgeBase:
    def test_at_06_subject_tree_by_field_grade(self, auth_client):
        r = auth_client.get("/api/v1/subjects?field=ریاضی&grade=دوازدهم")
        assert r.status_code == 200
        subjects = r.json()["data"]
        assert len(subjects) > 0
        assert all(s["field"] == "ریاضی" and s["grade"] == "دوازدهم" for s in subjects)
        names = {s["name"] for s in subjects}
        assert "حسابان" in names
        # فصل‌ها و مباحث
        subject_id = subjects[0]["id"]
        r = auth_client.get(f"/api/v1/subjects/{subject_id}/chapters")
        assert r.status_code == 200

    def test_at_07_import_valid_book(self, auth_client):
        result = _import_sample_book(auth_client)
        assert result["questions"] == 8
        assert result["chapters"] == 2
        assert result["topics"] == 3

    def test_at_08_invalid_book_persian_error(self, auth_client):
        r = auth_client.post("/api/v1/resources/import-book", json={"title": "کتاب بدون فصل"})
        assert r.status_code == 422
        assert r.json()["success"] is False
        message = r.json()["error"]["message"]
        assert any("\u0600" <= ch <= "\u06FF" for ch in message)

    def test_at_09_resource_questions(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        assert len(questions) == 8
        q = questions[0]
        assert q["topic_title"]
        assert q["difficulty"] in ("easy", "medium", "hard")

    def test_duplicate_book_warns(self, auth_client):
        # قانون ۸.۵: کتاب تکراری هشدار + گزینه به‌روزرسانی
        book = copy.deepcopy(SAMPLE_BOOK)
        book["title"] = f"کتاب تکراری — {uuid.uuid4().hex[:6]}"
        _import_sample_book(auth_client, book)
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422
        assert r.json()["error"]["details"].get("duplicate") is True
        # به‌روزرسانی با پرچم
        r = auth_client.post(
            "/api/v1/resources/import-book?update_existing=true", json=book)
        assert r.status_code == 200
        assert r.json()["data"]["updated"] is True


# ============ ۱۰.۳ ثبت تست و مرور ============

def _record_tests(auth_client, questions: list[dict]) -> None:
    q = {x["number"] + "|" + x["topic_title"]: x for x in questions}
    items = list(questions)
    payload = {"records": [
        {"question_id": items[0]["id"], "result": "correct"},
        {"question_id": items[1]["id"], "result": "wrong", "error_type": "careless",
         "marks": ["important", "hard"]},
        {"question_id": items[2]["id"], "result": "correct", "marks": ["tip"]},
        {"question_id": items[3]["id"], "result": "wrong", "error_type": "forgotten"},
        {"question_id": items[4]["id"], "result": "blank"},
    ]}
    r = auth_client.post("/api/v1/test-records", json=payload)
    assert r.status_code == 200, r.text


class TestActivityReview:
    def test_at_10_11_12_record_tests(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        _record_tests(auth_client, questions)
        r = auth_client.get("/api/v1/test-records")
        records = r.json()["data"]
        assert len(records) == 5
        wrong = [x for x in records if x["result"] == "wrong"]
        assert len(wrong) == 2
        assert all(x["error_type"] in ("careless", "forgotten") for x in wrong)

    def test_error_type_only_for_wrong(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        r = auth_client.post("/api/v1/test-records", json={"records": [
            {"question_id": questions[0]["id"], "result": "correct", "error_type": "careless"},
        ]})
        assert r.status_code == 422  # قانون ۸.۳

    def test_marks_add_remove(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        qid = questions[0]["id"]
        r = auth_client.post(f"/api/v1/questions/{qid}/marks", json={"mark_type": "important"})
        assert r.status_code == 200
        # چند تیک همزمان
        auth_client.post(f"/api/v1/questions/{qid}/marks", json={"mark_type": "hard"})
        r = auth_client.get(f"/api/v1/questions/{qid}/marks")
        assert {m["mark_type"] for m in r.json()["data"]} == {"important", "hard"}
        r = auth_client.delete(f"/api/v1/questions/{qid}/marks/important")
        assert r.status_code == 200
        r = auth_client.get(f"/api/v1/questions/{qid}/marks")
        assert {m["mark_type"] for m in r.json()["data"]} == {"hard"}

    def test_at_13_rebuild_review_queue(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        _record_tests(auth_client, questions)
        r = auth_client.post("/api/v1/reviews/rebuild")
        assert r.status_code == 200
        r = auth_client.get("/api/v1/reviews/queue")
        items = r.json()["data"]
        # ۲ غلط + ۲ تیک (important/hard روی سوال غلط → همان سوال) + ۱ تیک tip (در صف نمی‌آید)
        assert len(items) >= 2
        reasons = {i["reason"] for i in items}
        assert "wrong" in reasons
        # اولویت‌ها نزولی
        priorities = [i["priority"] for i in items]
        assert priorities == sorted(priorities, reverse=True)

    def test_at_14_complete_review(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        _record_tests(auth_client, questions)
        auth_client.post("/api/v1/reviews/rebuild")
        r = auth_client.get("/api/v1/reviews/queue")
        first_item = r.json()["data"][0]
        r = auth_client.post(f"/api/v1/reviews/{first_item['id']}/complete")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "done"
        # از صف فعال خارج شد
        r = auth_client.get("/api/v1/reviews/queue")
        assert first_item["id"] not in [i["id"] for i in r.json()["data"]]
        # بازگرداندن به صف (قانون ۸.۲ بند ۵)
        r = auth_client.post(f"/api/v1/reviews/{first_item['id']}/reopen")
        assert r.status_code == 200
        r = auth_client.get("/api/v1/reviews/queue")
        assert first_item["id"] in [i["id"] for i in r.json()["data"]]


# ============ ۱۰.۴ برنامه‌ریزی ============

class TestPlanning:
    def test_at_15_weekly_goal(self, auth_client):
        today = dt.date.today()
        r = auth_client.post("/api/v1/goals", json={
            "type": "weekly", "title": "تمرین حد — ۱۰ تست",
            "target_value": {"minutes": 180, "subject": "حسابان"},
            "start_date": today.isoformat(),
            "end_date": (today + dt.timedelta(days=6)).isoformat(),
        })
        assert r.status_code == 200, r.text
        goal = r.json()["data"]
        assert goal["type"] == "weekly"
        r = auth_client.get("/api/v1/goals?type=weekly")
        assert any(g["id"] == goal["id"] for g in r.json()["data"])

    def test_at_16_school_time_blocks(self, auth_client):
        r = auth_client.put("/api/v1/time-blocks", json={"blocks": [
            {"day_of_week": 0, "start_time": "07:30", "end_time": "13:30",
             "block_type": "school", "title": "مدرسه"},
            {"day_of_week": 2, "start_time": "16:00", "end_time": "18:00",
             "block_type": "class", "title": "کلاس ریاضی"},
        ]})
        assert r.status_code == 200, r.text
        r = auth_client.get("/api/v1/time-blocks")
        blocks = r.json()["data"]
        assert len(blocks) == 2
        assert blocks[0]["day_of_week"] == 0  # شنبه

    def test_at_17_generate_week_plan(self, auth_client):
        # بلوک‌های زمانی
        auth_client.put("/api/v1/time-blocks", json={"blocks": [
            {"day_of_week": 0, "start_time": "07:30", "end_time": "13:30",
             "block_type": "school", "title": "مدرسه"},
        ]})
        # هدف هفتگی
        today = dt.date.today()
        monday = today + dt.timedelta(days=1)
        auth_client.post("/api/v1/goals", json={
            "type": "weekly", "title": "مطالعه حسابان",
            "target_value": {"minutes": 3000, "subject": "حسابان"},
            "start_date": today.isoformat(),
            "end_date": (today + dt.timedelta(days=6)).isoformat(),
        })
        # شنبه این هفته (هفته ایرانی)
        from app.core.jalali import week_start as iran_week_start

        week_start = iran_week_start(today)
        r = auth_client.post("/api/v1/plans/generate-week", json={
            "week_start": week_start.isoformat()})
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert len(data["plans"]) == 7
        # شنبه (روز اول) به خاطر مدرسه آیتم کمتری دارد
        sat_items = data["plans"][0]["items"]
        sun_items = data["plans"][1]["items"]
        assert len(sat_items) <= len(sun_items)

    def test_at_18_edit_day_plan(self, auth_client):
        day = dt.date.today().isoformat()
        r = auth_client.put(f"/api/v1/plans/{day}", json={
            "items": [{"start": "16:00", "end": "17:30", "title": "ریاضی — حد",
                       "subject": "حسابان", "type": "study"}],
            "status": "active",
        })
        assert r.status_code == 200, r.text
        r = auth_client.get(f"/api/v1/plans?date={day}")
        plan = r.json()["data"]
        assert plan["items"][0]["title"] == "ریاضی — حد"
        assert plan["summary"]["total_minutes"] == 90


# ============ ۱۰.۵ آزمون و نمره‌دهی ============

class TestExam:
    def _create_exam(self, auth_client) -> tuple[str, list[dict]]:
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        r = auth_client.post("/api/v1/exams", json={
            "title": "آزمون آزمایشی حسابان", "exam_type": "mock",
            "duration_minutes": 60,
            "question_ids": [q["id"] for q in questions],
        })
        assert r.status_code == 200, r.text
        return r.json()["data"]["id"], questions

    def test_at_19_create_exam(self, auth_client):
        exam_id, questions = self._create_exam(auth_client)
        r = auth_client.get(f"/api/v1/exams/{exam_id}")
        assert r.json()["data"]["question_count"] == 8
        assert r.json()["data"]["status"] == "planned"

    def test_at_20_21_22_submit_and_score(self, auth_client):
        exam_id, questions = self._create_exam(auth_client)
        auth_client.post(f"/api/v1/exams/{exam_id}/start")
        # ۸ سوال: ۵ درست، ۲ غلط، ۱ نزده
        answers = []
        results = ["correct", "correct", "wrong", "correct", "wrong",
                   "correct", "correct", "blank"]
        for q, res in zip(questions, results):
            answers.append({"question_id": q["id"], "result": res})
        r = auth_client.post(f"/api/v1/exams/{exam_id}/submit", json={"answers": answers})
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["correct_count"] == 5
        assert data["wrong_count"] == 2
        assert data["blank_count"] == 1
        # AT-21: (5 - 0.33*2)/8*100 = 54.25
        assert data["percent_konkur"] == pytest.approx(54.25, abs=0.01)
        assert data["percent_no_penalty"] == pytest.approx(62.5, abs=0.01)
        # AT-22: تحلیل سختی
        breakdown = data["difficulty_breakdown"]
        assert breakdown["easy"]["total"] + breakdown["medium"]["total"] + breakdown["hard"]["total"] == 8
        # نتیجه کامل
        r = auth_client.get(f"/api/v1/exams/{exam_id}/result")
        assert r.json()["data"]["by_subject"]

    def test_max_questions_limit_configurable(self, auth_client):
        # محدودیت ۸.۷ — حداکثر سوال آزمون از تنظیمات خوانده می‌شود (قابل تنظیم)
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        # کاهش سقف به ۵ و تست عبور از سقف
        auth_client.put("/api/v1/settings", json={"exam_policy": {"max_questions": 5}})
        r = auth_client.post("/api/v1/exams", json={
            "title": "آزمون بزرگ", "exam_type": "mock", "duration_minutes": 60,
            "question_ids": [q["id"] for q in questions],  # ۸ سوال > ۵
        })
        assert r.status_code == 422
        # بازگردانی سقف پیش‌فرض
        auth_client.put("/api/v1/settings", json={"exam_policy": {"max_questions": 200}})


# ============ ۱۰.۶ تحلیل، گزارش و Backup ============

class TestAnalyticsReportsBackup:
    def _prepare_data(self, auth_client):
        result = _import_sample_book(auth_client)
        questions = _get_questions(auth_client, result["resource_id"])
        auth_client.post("/api/v1/test-records", json={"records": [
            {"question_id": questions[0]["id"], "result": "correct"},
            {"question_id": questions[1]["id"], "result": "wrong", "error_type": "careless"},
            {"question_id": questions[2]["id"], "result": "blank"},
        ]})
        return questions

    def test_at_23_subject_stats(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/analytics/by-subject")
        assert r.status_code == 200
        subjects = r.json()["data"]
        assert len(subjects) >= 1
        row = next(s for s in subjects if s["total"] >= 3)
        assert row["correct"] + row["wrong"] + row["blank"] == row["total"]
        assert row["percent_konkur"] is not None

    def test_analytics_endpoints(self, auth_client):
        self._prepare_data(auth_client)
        for path in ("/api/v1/analytics/overview", "/api/v1/analytics/by-topic",
                     "/api/v1/analytics/difficulty", "/api/v1/analytics/mistake-types"):
            r = auth_client.get(path)
            assert r.status_code == 200, path
        r = auth_client.get("/api/v1/analytics/mistake-types")
        types = r.json()["data"]
        assert any(t["error_type"] == "careless" for t in types)

    def test_at_24_weekly_report(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/reports/weekly")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["tests"]["total"] == 3
        # هفته ناقص: روزهای موجود تا امروز (قانون ۸.۶)
        assert 1 <= len(data["per_day"]) <= 7
        # هفته کامل گذشته: ۷ روز شنبه تا جمعه
        past_week = dt.date.today() - dt.timedelta(days=14)
        r = auth_client.get(f"/api/v1/reports/weekly?week_start={past_week.isoformat()}")
        assert len(r.json()["data"]["per_day"]) == 7

    def test_daily_and_monthly_reports(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/reports/daily")
        assert r.status_code == 200
        assert "date_label" in r.json()["data"]
        today = dt.date.today()
        jy, jm, _ = today.year + 621, None, None  # تبدیل ساده برای تست
        from app.core.jalali import to_jalali

        jy, jm, _jd = to_jalali(today)
        r = auth_client.get(f"/api/v1/reports/monthly?year={jy}&month={jm}")
        assert r.status_code == 200

    def test_at_25_pdf_export(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/export/pdf?type=weekly")
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/pdf"
        assert r.content[:4] == b"%PDF"

    def test_excel_export(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/export/excel")
        assert r.status_code == 200
        assert r.content[:2] == b"PK"  # xlsx = zip

    def test_at_26_json_export(self, auth_client):
        self._prepare_data(auth_client)
        r = auth_client.get("/api/v1/export/json")
        assert r.status_code == 200
        data = r.json()
        assert "test_records" in data and len(data["test_records"]) == 3
        assert "knowledge_base" in data
        assert len(data["knowledge_base"]["questions"]) >= 8

    def test_at_27_backup_and_restore(self, auth_client, client):
        self._prepare_data(auth_client)
        # ایجاد پشتیبان
        r = auth_client.post("/api/v1/backup/create", json={})
        assert r.status_code == 200, r.text
        backup = r.json()["data"]
        assert backup["filename"].startswith("alems-backup-")
        # فهرست
        r = auth_client.get("/api/v1/backup/list")
        assert any(b["id"] == backup["id"] for b in r.json()["data"])
        # دانلود
        r = auth_client.get(f"/api/v1/backup/download/{backup['id']}")
        assert r.status_code == 200
        # بازگردانی بدون تأیید رد می‌شود (تأیید دومرحله‌ای)
        r = auth_client.post("/api/v1/backup/restore", json={
            "backup_id": backup["id"], "confirm": False})
        assert r.status_code == 422
        # بازگردانی با تأیید
        r = auth_client.post("/api/v1/backup/restore", json={
            "backup_id": backup["id"], "confirm": True})
        assert r.status_code == 200, r.text
        # داده‌ها بازگشته‌اند
        r = auth_client.get("/api/v1/test-records")
        assert len(r.json()["data"]) == 3

    def test_backup_encrypted(self, auth_client):
        r = auth_client.post("/api/v1/backup/create", json={
            "encrypted": True, "password": "test1234"})
        assert r.status_code == 200
        assert r.json()["data"]["encrypted"] is True
        assert r.json()["data"]["filename"].endswith(".zip")


# ============ موارد عمومی ============

class TestGeneral:
    def test_unauthorized_persian(self, client):
        r = client.get("/api/v1/test-records")
        assert r.status_code == 401
        assert any("\u0600" <= ch <= "\u06FF" for ch in r.json()["error"]["message"])

    def test_envelope_shape(self, auth_client):
        r = auth_client.get("/api/v1/subjects")
        body = r.json()
        assert set(body.keys()) == {"success", "data", "error", "meta"}

    def test_pagination(self, auth_client):
        _import_sample_book(auth_client)
        r = auth_client.get("/api/v1/resources/00000000-0000-0000-0000-000000000000/questions")
        # منبع ناموجود → 404 فارسی
        assert r.status_code == 404
