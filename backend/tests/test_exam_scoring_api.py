"""تست‌های API نمره‌دهی آزمون — AT-20/21/22 + قوانین سند 08 §8.5/§8.6.

فرمول‌های اجباری:
    percent_konkur     = (correct − 0.33 × wrong) / total × 100
    percent_no_penalty = correct / total × 100
    total = 0 → None (قانون ۸.۶: درصد ۰ یا null)؛ درصد منفی همان‌طور برگردانده می‌شود.
"""
from __future__ import annotations

import copy
import uuid

import pytest


def _uname() -> str:
    return f"ex_{uuid.uuid4().hex[:8]}"


def _book(n: int = 9, with_difficulty: bool = True) -> dict:
    """کتاب n سوالی با سختی چرخشی easy/medium/hard."""
    diffs = ["easy", "medium", "hard"]
    questions = []
    for i in range(1, n + 1):
        q = {"number": str(i), "answer": "1"}
        if with_difficulty:
            q["difficulty"] = diffs[(i - 1) % 3]
        questions.append(q)
    return {"title": f"کتاب آزمون {n}", "chapters": [
        {"title": "ف۱", "topics": [{"title": "م۱", "questions": questions}]}]}


def _all_questions(c, rid: str) -> list[dict]:
    """دریافت همه سوالات منبع با درنظرگرفتن صفحه‌بندی (حداکثر 200 در صفحه)."""
    out, page = [], 1
    while True:
        r = c.get(f"/api/v1/resources/{rid}/questions",
                  params={"page": page, "page_size": 200}).json()["data"]
        out.extend(r)
        if len(r) < 200:
            return out
        page += 1


@pytest.fixture()
def exam_env(client):
    """کاربر + کتاب ۹ سوالی؛ خروجی: client, question_ids."""
    uname = _uname()
    client.post("/api/v1/auth/register", json={"username": uname, "password": "secret123"})
    r = client.post("/api/v1/auth/login", json={"username": uname, "password": "secret123"})
    client.headers.update({"Authorization": f"Bearer {r.json()['data']['access_token']}"})

    # سیاست آزمون را صریح ۲۰۰ می‌کنیم (تست‌های تنظیمات ممکن است آن را تغییر داده باشند)
    settings = client.get("/api/v1/settings").json()["data"]
    client.put("/api/v1/settings", json={
        **settings, "exam_policy": {**settings["exam_policy"], "max_questions": 200}})

    book = _book()
    book["title"] += f" — {uuid.uuid4().hex[:6]}"
    rid = client.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
    questions = _all_questions(client, rid)
    return {"client": client, "questions": questions}


def _create_exam(c, questions: list[dict], title: str = "آزمون آزمایشی") -> dict:
    r = c.post("/api/v1/exams", json={
        "title": title, "exam_type": "mock", "duration_minutes": 60,
        "question_ids": [q["id"] for q in questions]})
    assert r.status_code == 200, r.text
    return r.json()["data"]


def _answers(questions: list[dict], pattern: list[str]) -> list[dict]:
    return [{"question_id": q["id"], "result": res}
            for q, res in zip(questions, pattern)]


class TestExamFlow:
    """جریان کامل: ایجاد → شروع → ارسال پاسخ → نتیجه (AT-19/20)."""

    def test_create_start_submit_flow(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        exam = _create_exam(c, qs[:4])
        assert exam["status"] == "planned"
        assert exam["question_count"] == 4

        r = c.post(f"/api/v1/exams/{exam['id']}/start")
        assert r.status_code == 200
        assert r.json()["data"]["status"] == "in_progress"

        r = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(qs[:4], [
            "correct", "wrong", "correct", "blank"])})
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["correct_count"] == 2
        assert data["wrong_count"] == 1
        assert data["blank_count"] == 1

    def test_result_endpoint_matches_submit(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        exam = _create_exam(c, qs[:3])
        c.post(f"/api/v1/exams/{exam['id']}/start")
        submitted = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            qs[:3], ["correct", "correct", "wrong"])}).json()["data"]
        fetched = c.get(f"/api/v1/exams/{exam['id']}/result").json()["data"]["result"]
        assert fetched["percent_konkur"] == submitted["percent_konkur"]
        assert fetched["correct_count"] == submitted["correct_count"]


class TestScoringFormula:
    """فرمول‌های اجباری — دقیق و با حالت‌های خاص (AT-21)."""

    def test_known_percent_exact(self, exam_env):
        """۶ درست، ۲ غلط، ۲ نزده از ۱۰ → (6 − 0.33×2)/10×100 = 53.4."""
        c = exam_env["client"]
        # کتاب ۱۰ سوالی جدا
        book = _book(10)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        rid = c.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
        qs = _all_questions(c, rid)
        exam = _create_exam(c, qs, "محاسبه دقیق")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        pattern = ["correct"] * 6 + ["wrong"] * 2 + ["blank"] * 2
        data = c.post(f"/api/v1/exams/{exam['id']}/submit",
                      json={"answers": _answers(qs, pattern)}).json()["data"]
        assert data["percent_konkur"] == pytest.approx(53.4)
        assert data["percent_no_penalty"] == pytest.approx(60.0)

    def test_negative_percent_kept(self, exam_env):
        """همه غلط → درصد منفی همان‌طور برمی‌گردد (قانون ۸.۶)."""
        c, qs = exam_env["client"], exam_env["questions"]
        exam = _create_exam(c, qs[:6], "همه غلط")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        data = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            qs[:6], ["wrong"] * 6)}).json()["data"]
        assert data["percent_konkur"] == pytest.approx(-33.0)
        assert data["percent_no_penalty"] == pytest.approx(0.0)

    def test_all_blank_zero_percent(self, exam_env):
        """همه نزده → (0 − 0)/total = صفر؛ نه منفی، نه None."""
        c, qs = exam_env["client"], exam_env["questions"]
        exam = _create_exam(c, qs[:5], "همه نزده")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        data = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            qs[:5], ["blank"] * 5)}).json()["data"]
        assert data["percent_konkur"] == pytest.approx(0.0)
        assert data["percent_no_penalty"] == pytest.approx(0.0)

    def test_all_correct_100(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        exam = _create_exam(c, qs[:4], "همه درست")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        data = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            qs[:4], ["correct"] * 4)}).json()["data"]
        assert data["percent_konkur"] == pytest.approx(100.0)
        assert data["percent_no_penalty"] == pytest.approx(100.0)


class TestDifficultyPerformance:
    """تحلیل سختی (AT-22) — سوال بدون سختی نادیده گرفته می‌شود (قانون ۸.۶)."""

    def test_breakdown_per_difficulty(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        # سختی چرخشی است: اندیس‌های 0,3,6 easy / 1,4,7 medium / 2,5,8 hard
        # easy: 3 درست (۱۰۰) — medium: 1 درست 2 غلط — hard: همه نزده (۰)
        pattern = ["correct", "correct", "blank",
                   "correct", "wrong", "blank",
                   "correct", "wrong", "blank"]
        exam = _create_exam(c, qs, "تفکیک سختی")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        data = c.post(f"/api/v1/exams/{exam['id']}/submit",
                      json={"answers": _answers(qs, pattern)}).json()["data"]
        bd = data["difficulty_breakdown"]
        assert set(bd.keys()) == {"easy", "medium", "hard"}
        assert bd["easy"]["correct"] == 3
        assert bd["easy"]["percent_konkur"] == pytest.approx(100.0)
        assert bd["medium"]["percent_konkur"] == pytest.approx(11.33)  # رُند ۲ رقم
        assert bd["hard"]["percent_konkur"] == pytest.approx(0.0)

    def test_questions_without_difficulty_ignored_in_breakdown(self, exam_env):
        c = exam_env["client"]
        book = _book(4, with_difficulty=False)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        rid = c.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
        qs = _all_questions(c, rid)
        exam = _create_exam(c, qs, "بدون سختی")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        data = c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            qs, ["correct"] * 4)}).json()["data"]
        assert all(b["total"] == 0 for b in data["difficulty_breakdown"].values())
        assert data["correct_count"] == 4  # نمره‌دهی کلی سالم است

    def test_analytics_difficulty_endpoint(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        # آزمون فقط با سوالات easy (اندیس‌های 0,3,6) — medium/hard هیچ رکوردی ندارند
        easy_qs = [qs[i] for i in (0, 3, 6)]
        exam = _create_exam(c, easy_qs, "تحلیل endpoint")
        c.post(f"/api/v1/exams/{exam['id']}/start")
        c.post(f"/api/v1/exams/{exam['id']}/submit", json={"answers": _answers(
            easy_qs, ["correct", "correct", "correct"])})
        r = c.get("/api/v1/analytics/difficulty")
        assert r.status_code == 200
        rows = r.json()["data"]
        by_key = {row["difficulty"]: row for row in rows}
        assert by_key["easy"]["total"] == 3
        assert by_key["easy"]["percent_konkur"] == pytest.approx(100.0)
        # سختی بدون هیچ داده → null (قانون ۸.۶)
        assert by_key["hard"]["percent_konkur"] is None
        assert by_key["hard"]["total"] == 0


class TestExamLimits:
    """محدودیت‌های آزمون — حداکثر ۲۰۰ سوال."""

    def test_201_questions_rejected(self, exam_env):
        c = exam_env["client"]
        book = _book(201)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        rid = c.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
        qs = _all_questions(c, rid)
        assert len(qs) == 201
        r = c.post("/api/v1/exams", json={
            "title": "بیش از حد", "exam_type": "mock", "duration_minutes": 90,
            "question_ids": [q["id"] for q in qs]})
        assert r.status_code == 422
        assert "200" in r.text  # پیام: حداکثر تعداد سوال در یک آزمون 200 است

    def test_200_questions_accepted(self, exam_env):
        c = exam_env["client"]
        book = _book(200)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        rid = c.post("/api/v1/resources/import-book", json=book).json()["data"]["resource_id"]
        qs = _all_questions(c, rid)
        r = c.post("/api/v1/exams", json={
            "title": "مرز مجاز", "exam_type": "mock", "duration_minutes": 120,
            "question_ids": [q["id"] for q in qs]})
        assert r.status_code == 200, r.text
        assert r.json()["data"]["question_count"] == 200

    def test_empty_question_list_rejected(self, exam_env):
        r = exam_env["client"].post("/api/v1/exams", json={
            "title": "خالی", "exam_type": "mock", "question_ids": []})
        assert r.status_code == 422

    def test_duplicate_question_ids_deduped(self, exam_env):
        c, qs = exam_env["client"], exam_env["questions"]
        r = c.post("/api/v1/exams", json={
            "title": "تکراری", "exam_type": "mock", "duration_minutes": 30,
            "question_ids": [qs[0]["id"], qs[0]["id"], qs[1]["id"]]})
        assert r.status_code == 200
        assert r.json()["data"]["question_count"] == 2
