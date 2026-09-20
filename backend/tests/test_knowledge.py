"""تست‌های پذیرش و واحد فاز ۲ — Knowledge Base (AT-06 تا AT-09 + الزامات ویژه)."""
from __future__ import annotations

import copy
import uuid

import pytest


def _uname() -> str:
    return f"kb_{uuid.uuid4().hex[:8]}"


# ---------- کتاب نمونه با زیرمبحث (۲ فصل، ۱۰ سوال) ----------

SUBTOPIC_BOOK = {
    "title": "کتاب تست درخت — نمونه فاز ۲",
    "publisher": "نشر ممیزی",
    "subject": "حسابان",
    "chapters": [
        {
            "title": "فصل تابع",
            "topics": [
                {
                    "title": "تعریف تابع",
                    "questions": [
                        {"number": "1", "answer": "2", "difficulty": "آسان", "importance": 2,
                         "tags": ["تابع"], "text": "کدام رابطه تابع است؟"},
                        {"number": "2", "answer": "3", "difficulty": "متوسط"},
                        {"number": "3", "answer": "1", "difficulty": "سخت", "importance": 5},
                    ],
                },
                {
                    "title": "دامنه و برد",
                    "questions": [
                        {"number": "1", "answer": "4", "difficulty": "متوسط"},
                    ],
                    "subtopics": [
                        {
                            "title": "دامنه توابع جبری",
                            "questions": [
                                {"number": "1", "answer": "3", "difficulty": "آسان"},
                                {"number": "2", "answer": "2", "difficulty": "متوسط"},
                            ],
                        },
                        {
                            "title": "برد تابع",
                            "questions": [
                                {"number": "1", "answer": "1", "difficulty": "سخت"},
                                {"number": "2", "answer": "5", "difficulty": "متوسط"},
                            ],
                        },
                    ],
                },
            ],
        },
        {
            "title": "فصل حد",
            "topics": [
                {
                    "title": "حد در بی‌نهایت",
                    "questions": [
                        {"number": "1", "answer": "3", "difficulty": "سخت", "importance": 5},
                        {"number": "2", "answer": "2", "difficulty": "متوسط"},
                        {"number": "3", "answer": "1", "difficulty": "آسان"},
                    ],
                },
            ],
        },
    ],
}


@pytest.fixture()
def kb_auth_client(auth_client):
    """کلاینت احراز هویت‌شده با پروفایل کامل ریاضی/دوازدهم."""
    return auth_client


class TestBookImport:
    """الزام ۱ و ۲ — Schema واضح + import کامل."""

    def test_import_with_subtopics(self, auth_client):
        """درخت کامل: فصل ← مبحث ← زیرمبحث؛ تعداد سوالات درست."""
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 200, r.text
        data = r.json()["data"]
        assert data["chapters"] == 2
        assert data["topics"] == 3  # مبحث سطح بالا: تعریف تابع، دامنه و برد، حد در بی‌نهایت
        assert data["questions"] == 11
        # resource به درس «حسابان» متصل شده
        assert data["subject_matched"] == "حسابان"

    def test_subtopic_has_parent_id(self, auth_client):
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        resource_id = r.json()["data"]["resource_id"]

        r = auth_client.get(f"/api/v1/resources/{resource_id}/tree")
        assert r.status_code == 200
        tree = r.json()["data"]
        titles = {ch["title"] for ch in tree["chapters"]}
        assert titles == {"فصل تابع", "فصل حد"}

        # مبحث «دامنه و برد» باید دو زیرمبحث با parent_id داشته باشد
        damene = next(
            t for ch in tree["chapters"] for t in ch["topics"] if t["title"] == "دامنه و برد"
        )
        assert {st["title"] for st in damene["subtopics"]} == {"دامنه توابع جبری", "برد تابع"}
        assert all(st["parent_id"] == damene["id"] for st in damene["subtopics"])
        assert damene["subtopics"][0]["question_count"] == 2

    def test_nested_subtopic_rejected(self, auth_client):
        """زیرِ زیرمبحث مجاز نیست (درخت سند فقط تا زیرمبحث است)."""
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        book["chapters"][0]["topics"][1]["subtopics"][0]["subtopics"] = [
            {"title": "غیرمجاز", "questions": [{"number": "1", "answer": "1"}]},
        ]
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422
        assert "زیرمبحث" in r.json()["error"]["message"]

    def test_question_number_unique_across_subtopics(self, auth_client):
        """شماره سوال در مسیر مبحث←زیرمبحث یکتا اعتبارسنجی می‌شود."""
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        # تکرار شماره در زیرمبحث همان مبحث
        book["chapters"][0]["topics"][1]["subtopics"][0]["questions"].append(
            {"number": "1", "answer": "2"})
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422

    def test_import_schema_endpoint(self, client):
        """الزام ۱ — Schema رسمی قابل دریافت است."""
        r = client.get("/api/v1/resources/import-book/schema")
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["schema"]["required"] == ["title", "chapters"]
        assert "chapter" in data["schema"]["definitions"]
        assert "subtopics" in data["schema"]["definitions"]["topic"]["properties"]
        # نمونه ۱۰ سواله
        sample = data["sample"]
        total = sum(
            len(t.get("questions", [])) + sum(len(st["questions"]) for st in t.get("subtopics", []))
            for ch in sample["chapters"] for t in ch["topics"]
        )
        assert len(sample["chapters"]) == 2
        assert total >= 10  # الزام: حداقل ۱۰ سوال


class TestDuplicateBook:
    """الزام ۳ — هشدار کتاب تکراری."""

    def test_duplicate_conflict_with_options(self, auth_client):
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        r1 = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r1.status_code == 200

        # ورود مجدد بدون پرچم → 409 + گزینه به‌روزرسانی
        r2 = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r2.status_code == 409
        body = r2.json()
        assert body["success"] is False
        assert body["error"]["details"]["duplicate"] is True
        assert "به‌روزرسانی" in body["error"]["message"]

        # با پرچم → به‌روزرسانی موفق
        r3 = auth_client.post(
            "/api/v1/resources/import-book?update_existing=true", json=book)
        assert r3.status_code == 200
        assert r3.json()["data"]["updated"] is True
        assert r3.json()["data"]["questions"] == 11


class TestTreeFilter:
    """الزام ۴ — فیلتر درخت بر اساس رشته و پایه."""

    def test_subjects_filtered_by_field_grade(self, client):
        r = client.get("/api/v1/subjects", params={"field": "تجربی", "grade": "یازدهم"})
        assert r.status_code == 200
        subjects = r.json()["data"]
        assert len(subjects) > 0
        assert all(s["field"] == "تجربی" and s["grade"] == "یازدهم" for s in subjects)
        names = {s["name"] for s in subjects}
        assert "زیست" in names  # درس اختصاصی تجربی
        assert "حسابان" in names

    def test_filter_excludes_other_fields(self, client):
        r_riazi = client.get("/api/v1/subjects", params={"field": "ریاضی", "grade": "دوازدهم"})
        r_ensani = client.get("/api/v1/subjects", params={"field": "انسانی", "grade": "دوازدهم"})
        riazzi_names = {s["name"] for s in r_riazi.json()["data"]}
        ensani_names = {s["name"] for s in r_ensani.json()["data"]}
        # درس اختصاصی هر رشته در رشته دیگر نیست
        assert "گسسته" in riazzi_names and "گسسته" not in ensani_names
        assert "جامعه‌شناسی" in ensani_names and "جامعه‌شناسی" not in riazzi_names

    def test_chapter_topic_traversal(self, client, auth_client):
        """پیمایش درخت: درس → فصل → مبحث (AT-06)."""
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        resource_id = r.json()["data"]["resource_id"]

        # درس و فصلِ کتاب از درخت خودِ منبع (فصل/مبحث در سطح درس مشترک‌اند؛
        # درخت منبع شناسه دقیق گره‌های این کتاب را می‌دهد)
        tree = client.get(f"/api/v1/resources/{resource_id}/tree").json()["data"]
        subject_id = tree["subject"]["id"]
        tree_chapter = next(
            ch for ch in tree["chapters"] if ch["title"] == "فصل تابع")

        # پیمایش با endpointهای عمومی درخت: درس → فصل → مبحث
        r = client.get(f"/api/v1/subjects/{subject_id}/chapters")
        chapters = r.json()["data"]
        assert any(c["id"] == tree_chapter["id"] for c in chapters)

        r = client.get(f"/api/v1/chapters/{tree_chapter['id']}/topics")
        topics = r.json()["data"]
        top_titles = {t["title"] for t in topics if not t["parent_id"]}
        assert "تعریف تابع" in top_titles
        # زیرمباحث با parent_id
        subs = [t for t in topics if t["parent_id"]]
        assert {s["title"] for s in subs} == {"دامنه توابع جبری", "برد تابع"}

    def test_exact_subject_match_with_field_grade(self, auth_client):
        """اگر field/grade در فایل باشد، تطبیق درس دقیق انجام می‌شود."""
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        book["field"] = "ریاضی"
        book["grade"] = "دوازدهم"
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 200
        rid = r.json()["data"]["resource_id"]
        tree = auth_client.get(f"/api/v1/resources/{rid}/tree").json()["data"]
        assert tree["subject"]["name"] == "حسابان"
        assert tree["subject"]["grade"] == "دوازدهم"
        assert tree["subject"]["field"] == "ریاضی"


class TestClassification:
    """الزام ۵ — طبقه‌بندی سوال: سختی، اهمیت، تگ."""

    def test_classification_persisted(self, auth_client):
        book = copy.deepcopy(SUBTOPIC_BOOK)
        book["title"] += f" — {uuid.uuid4().hex[:6]}"
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        resource_id = r.json()["data"]["resource_id"]

        r = auth_client.get(f"/api/v1/resources/{resource_id}/questions?page_size=100")
        questions = r.json()["data"]
        assert len(questions) == 11

        # سختی‌ها حفظ شده‌اند
        difficulties = {q["difficulty"] for q in questions}
        assert difficulties == {"easy", "medium", "hard"}

        # اهمیت و تگ
        q1 = next(q for q in questions if q["number"] == "1" and q["topic_title"] == "تعریف تابع")
        assert q1["importance"] == 2
        assert "تابع" in q1["tags"]
        assert q1["text"] == "کدام رابطه تابع است؟"

        # سوال زیرمبحث، topic_title درست دارد
        sub_q = next(q for q in questions if q["topic_title"] == "دامنه توابع جبری")
        assert sub_q["parent_topic_id"] is not None

    def test_persian_difficulty_accepted(self, auth_client):
        """سختی فارسی (آسان/متوسط/سخت) هم پذیرفته می‌شود."""
        book = {
            "title": f"کتاب فارسی‌سختی — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{
                "title": "م۱",
                "questions": [{"number": "1", "answer": "2", "difficulty": "سخت"}],
            }]}],
        }
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 200
        rid = r.json()["data"]["resource_id"]
        r = auth_client.get(f"/api/v1/resources/{rid}/questions")
        assert r.json()["data"][0]["difficulty"] == "hard"

    def test_invalid_difficulty_rejected_persian(self, auth_client):
        book = {
            "title": f"کتاب بد — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{
                "title": "م۱",
                "questions": [{"number": "1", "answer": "2", "difficulty": "بسیار سخت"}],
            }]}],
        }
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422
        assert "سطح سختی" in r.json()["error"]["message"]

    def test_toc_only_import_succeeds(self, auth_client):
        """ورود فقط‌فهرست (بدون سوال) موفق است — مبحث/زیرمبحث خالی از سوال مجاز."""
        book = {
            "title": f"کتاب فقط‌فهرست — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{"title": "م۱", "questions": []}]}],
        }
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 200, r.text
        stats = r.json()["data"]
        assert stats["chapters"] == 1
        assert stats["topics"] == 1
        assert stats["questions"] == 0


class TestTocOnlyImport:
    """ورود کتاب فقط با فهرست مطالب — بدون هیچ سوالی (ساختار خالی مجاز)."""

    def _import(self, auth_client, book: dict) -> dict:
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 200, r.text
        return r.json()["data"]

    def test_full_toc_without_questions(self, auth_client):
        """مبحث فقط با زیرمبحث و بدون هیچ سوالی؛ زیرمبحث بدون کلید questions."""
        book = {
            "title": f"شیمی دهم — فقط فهرست — {uuid.uuid4().hex[:6]}",
            "subject": "شیمی",
            "chapters": [
                {"title": "فصل کیهان", "topics": [
                    {"title": "زنجیره غذایی", "subtopics": [
                        {"title": "ماده و نقش آن"},
                    ]},
                    {"title": "سوخت"},
                ]},
                {"title": "فصل آب", "topics": [
                    {"title": "هیدروکربن‌ها", "questions": [], "subtopics": [
                        {"title": "آلکان‌ها", "questions": []},
                    ]},
                ]},
            ],
        }
        stats = self._import(auth_client, book)
        assert stats["chapters"] == 2
        assert stats["topics"] == 3
        assert stats["subtopics"] == 2
        assert stats["questions"] == 0

    def test_toc_only_structure_visible_in_subject_tree(self, auth_client):
        """ساختار فقط‌فهرست در درخت درس با question_count صفر دیده می‌شود."""
        book = {
            "title": f"فیزیک — فهرست خالی — {uuid.uuid4().hex[:6]}",
            "subject": "حسابان",  # درس موجود در seed
            "chapters": [{"title": f"ف۱-{uuid.uuid4().hex[:6]}", "topics": [
                {"title": f"م۱-{uuid.uuid4().hex[:6]}", "subtopics": [{"title": "ز۱"}]},
            ]}],
        }
        stats = self._import(auth_client, book)
        rid = stats["resource_id"]
        hits = []
        for sbj in [x for x in auth_client.get("/api/v1/subjects").json()["data"]
                    if x["name"] == book["subject"]]:
            rows = auth_client.get(f"/api/v1/subjects/{sbj['id']}/chapters").json()["data"]
            hits += [c for c in rows if c["title"] == book["chapters"][0]["title"]]
        (ch,) = hits
        topics = auth_client.get(f"/api/v1/chapters/{ch['id']}/topics").json()["data"]
        (tp,) = [t for t in topics if t["title"] == book["chapters"][0]["topics"][0]["title"]]
        assert tp["title"].startswith("م۱")  # فقط عنوان، در درخت درس ثبت شده
        # سوالات منبع: خالی
        qs = auth_client.get(f"/api/v1/resources/{rid}/questions").json()["data"]
        assert qs == []

    def test_chapter_without_topics_allowed(self, auth_client):
        """فصل فقط با عنوان (بدون مبحث) هم مجاز است — گره خالی درخت."""
        book = {
            "title": f"فصل خالی — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": f"فص-جانبی-{uuid.uuid4().hex[:4]}"}],
        }
        stats = self._import(auth_client, book)
        assert stats["chapters"] == 1
        assert stats["topics"] == 0
        assert stats["questions"] == 0

    def test_regression_with_questions_still_works(self, auth_client):
        """رگرسیون: کتاب با سوال واقعی مثل قبل وارد می‌شود."""
        book = {
            "title": f"ریاضی — با سوال — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{
                "title": "م۱",
                "questions": [
                    {"number": "1", "answer": "2", "difficulty": "آسان"},
                    {"number": "2", "answer": "3"},
                ],
            }]}],
        }
        stats = self._import(auth_client, book)
        assert stats["questions"] == 2

    def test_incomplete_question_missing_answer_rejected(self, auth_client):
        """سوال ناقص (بدون answer) → خطای واضح فارسی."""
        book = {
            "title": f"ناقص — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{
                "title": "م۱",
                "questions": [{"number": "1"}],
            }]}],
        }
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422
        assert "پاسخ صحیح" in r.json()["error"]["message"]

    def test_questions_not_a_list_rejected(self, auth_client):
        """questions به‌شکل غیرفهرست → خطای واضح فارسی."""
        book = {
            "title": f"غیرفهرست — {uuid.uuid4().hex[:6]}",
            "chapters": [{"title": "ف۱", "topics": [{
                "title": "م۱", "questions": "سوال اول",
            }]}],
        }
        r = auth_client.post("/api/v1/resources/import-book", json=book)
        assert r.status_code == 422
        assert "فهرست" in r.json()["error"]["message"]
