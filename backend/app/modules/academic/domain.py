"""منطق دامنه دانش آموزشی — اعتبارسنجی و ادغام کتاب (خالص و قابل‌تست)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.academic.models import DIFFICULTIES, RESOURCE_TYPES
from app.shared.exceptions import ValidationError


@dataclass
class ImportedTopic:
    """مبحث استخراج‌شده از فایل کتاب — زیرمبحث‌ها یک سطح پایین‌تر."""

    title: str
    questions: list["ImportedQuestion"] = field(default_factory=list)
    subtopics: list["ImportedTopic"] = field(default_factory=list)

    def all_questions(self) -> list["ImportedQuestion"]:
        """سوالات مبحث + همه زیرمباحث."""
        return self.questions + [q for st in self.subtopics for q in st.questions]


@dataclass
class ImportedChapter:
    """فصل استخراج‌شده از فایل کتاب."""

    title: str
    order_index: int = 0
    topics: list[ImportedTopic] = field(default_factory=list)


@dataclass
class ImportedBook:
    """کتاب استخراج‌شده از فایل JSON — ورودی سرویس وارد کردن."""

    title: str
    publisher: str | None
    subject_name: str | None
    subject_field: str | None = None
    subject_grade: str | None = None
    resource_type: str = "book_test"
    chapters: list[ImportedChapter] = field(default_factory=list)

    @property
    def question_count(self) -> int:
        return sum(len(t.all_questions()) for ch in self.chapters for t in ch.topics)


@dataclass
class ImportedQuestion:
    """سوال استخراج‌شده."""

    number: str
    correct_answer: str
    difficulty: str | None = None
    importance: int = 1
    tags: list[str] = field(default_factory=list)
    text: str | None = None


def _clean(value) -> str:  # noqa: ANN001
    if value is None:
        return ""
    return str(value).strip()


def normalize_difficulty(raw) -> str | None:  # noqa: ANN001
    """نرمال‌سازی سطح سختی — آسان/متوسط/سخت یا None."""
    if raw is None or _clean(raw) == "":
        return None
    mapping = {
        "easy": "easy", "آسان": "easy", "1": "easy",
        "medium": "medium", "متوسط": "medium", "2": "medium",
        "hard": "hard", "سخت": "hard", "3": "hard",
    }
    value = mapping.get(_clean(raw).lower()) or mapping.get(_clean(raw))
    if value is None:
        raise ValidationError(f"سطح سختی نامعتبر است: «{raw}». مقادیر مجاز: آسان، متوسط، سخت.")
    return value


def normalize_answer(raw) -> str:  # noqa: ANN001
    """نرمال‌سازی پاسخ صحیح — عدد ۱ تا ۵ یا حرف."""
    value = _clean(raw)
    if not value:
        raise ValidationError("پاسخ صحیح سوال نمی‌تواند خالی باشد.")
    return value[:16]


def parse_importance(raw, default: int = 1) -> int:  # noqa: ANN001
    if raw in (None, ""):
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"مقدار اهمیت سوال باید عدد باشد: «{raw}»") from exc
    if not (1 <= value <= 5):
        raise ValidationError("اهمیت سوال باید عددی بین ۱ تا ۵ باشد.")
    return value


def _parse_questions(
    questions_raw, topic_path: str, seen_numbers: set[tuple[str, str]],
) -> list[ImportedQuestion]:
    """پارس فهرست سوالات یک مبحث/زیرمبحث با اعتبارسنجی کامل."""
    if not isinstance(questions_raw, list) or not questions_raw:
        raise ValidationError(f"«{topic_path}» باید حداقل یک سوال داشته باشد.")
    questions: list[ImportedQuestion] = []
    for q_raw in questions_raw:
        if not isinstance(q_raw, dict):
            raise ValidationError(f"سوال در «{topic_path}» باید یک شیء JSON باشد.")
        number = _clean(q_raw.get("number"))
        if not number:
            raise ValidationError(f"شماره سوال در «{topic_path}» الزامی است.")
        key = (topic_path, number)
        if key in seen_numbers:
            raise ValidationError(f"شماره سوال «{number}» در «{topic_path}» تکراری است.")
        seen_numbers.add(key)
        tags_raw = q_raw.get("tags", [])
        if not isinstance(tags_raw, list):
            tags_raw = [str(tags_raw)]
        questions.append(ImportedQuestion(
            number=number,
            correct_answer=normalize_answer(q_raw.get("answer", q_raw.get("correct_answer"))),
            difficulty=normalize_difficulty(q_raw.get("difficulty")),
            importance=parse_importance(q_raw.get("importance")),
            tags=[str(t) for t in tags_raw],
            text=_clean(q_raw.get("text")) or None,
        ))
    return questions


def _parse_topic(
    tp_raw, chapter_title: str, seen_numbers: set[tuple[str, str]],
) -> ImportedTopic:
    """پارس یک مبحث — با پشتیبانی اختیاری زیرمبحث (یک سطح، مطابق درخت سند)."""
    if not isinstance(tp_raw, dict):
        raise ValidationError(f"مبحث در فصل «{chapter_title}» باید یک شیء JSON باشد.")
    tp_title = _clean(tp_raw.get("title"))
    if not tp_title:
        raise ValidationError(f"عنوان مبحث در فصل «{chapter_title}» الزامی است.")
    topic = ImportedTopic(title=tp_title)
    topic.questions = _parse_questions(tp_raw.get("questions", []), tp_title, seen_numbers)

    # زیرمباحث اختیاری — فقط یک سطح (زیرِ زیرمبحث مجاز نیست)
    subtopics_raw = tp_raw.get("subtopics", [])
    if subtopics_raw:
        if not isinstance(subtopics_raw, list):
            raise ValidationError(f"«subtopics» مبحث «{tp_title}» باید یک فهرست باشد.")
        for st_raw in subtopics_raw:
            if not isinstance(st_raw, dict):
                raise ValidationError(f"زیرمبحث در «{tp_title}» باید یک شیء JSON باشد.")
            st_title = _clean(st_raw.get("title"))
            if not st_title:
                raise ValidationError(f"عنوان زیرمبحث در «{tp_title}» الزامی است.")
            st_path = f"{tp_title} - {st_title}"
            subtopic = ImportedTopic(title=st_title)
            subtopic.questions = _parse_questions(
                st_raw.get("questions", []), st_path, seen_numbers)
            if st_raw.get("subtopics"):
                raise ValidationError(
                    f"زیرمبحث «{st_title}» نمی‌تواند خودش زیرمبحث داشته باشد "
                    "(درخت فقط تا زیرمبحث است: درس ← فصل ← مبحث ← زیرمبحث)."
                )
            topic.subtopics.append(subtopic)
    return topic


def parse_book_json(data: dict) -> ImportedBook:
    """تبدیل JSON کتاب به ImportedBook — بدون دسترسی به دیتابیس (قابل‌تست).

    ساختار استاندارد فایل:
    {
      "title": "کتاب تست ...", "publisher": "انتشارات ...", "subject": "حسابان",
      "resource_type": "book_test",
      "chapters": [
        {"title": "فصل ۱", "topics": [
          {"title": "مبحث ۱", "questions": [
            {"number": "1", "answer": "2", "difficulty": "easy", "importance": 2,
             "tags": ["حد"], "text": "متن اختیاری"}
          ]}
        ]}
      ]
    }
    """
    if not isinstance(data, dict):
        raise ValidationError("فایل کتاب باید یک شیء JSON معتبر باشد.")
    title = _clean(data.get("title"))
    if not title:
        raise ValidationError("فیلد «title» (عنوان کتاب) الزامی است.")
    chapters_raw = data.get("chapters")
    if not isinstance(chapters_raw, list) or not chapters_raw:
        raise ValidationError("فهرست «chapters» الزامی است و باید حداقل یک فصل داشته باشد.")

    resource_type = _clean(data.get("resource_type")) or "book_test"
    if resource_type not in RESOURCE_TYPES:
        raise ValidationError(f"نوع منبع نامعتبر است: «{resource_type}».")

    book = ImportedBook(
        title=title,
        publisher=_clean(data.get("publisher")) or None,
        subject_name=_clean(data.get("subject")) or None,
        subject_field=_clean(data.get("field")) or None,
        subject_grade=_clean(data.get("grade")) or None,
        resource_type=resource_type,
    )

    seen_numbers: set[tuple[str, str]] = set()
    for ci, ch_raw in enumerate(chapters_raw):
        if not isinstance(ch_raw, dict):
            raise ValidationError(f"فصل شماره {ci + 1} باید یک شیء JSON باشد.")
        ch_title = _clean(ch_raw.get("title"))
        if not ch_title:
            raise ValidationError(f"عنوان فصل شماره {ci + 1} الزامی است.")
        chapter = ImportedChapter(title=ch_title, order_index=_clean(ch_raw.get("order_index")) or ci)
        topics_raw = ch_raw.get("topics", [])
        questions_direct = ch_raw.get("questions")
        # پشتیبانی از فصل‌های بدون مبحث: سوالات مستقیم زیر فصل
        if not topics_raw and isinstance(questions_direct, list):
            topics_raw = [{"title": ch_title, "questions": questions_direct}]
        if not isinstance(topics_raw, list) or not topics_raw:
            raise ValidationError(f"فصل «{ch_title}» باید حداقل یک مبحث داشته باشد. «سوالات بدون مبحث معتبر وارد نمی‌شوند.»")
        for ti, tp_raw in enumerate(topics_raw):
            chapter.topics.append(_parse_topic(tp_raw, ch_title, seen_numbers))
        book.chapters.append(chapter)

    if book.question_count == 0:
        raise ValidationError("کتاب باید حداقل یک سوال داشته باشد.")
    return book
