"""منطق دامنه دانش آموزشی — اعتبارسنجی و ادغام کتاب (خالص و قابل‌تست)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.modules.academic.models import DIFFICULTIES, RESOURCE_TYPES
from app.shared.exceptions import ValidationError


@dataclass
class ImportedTopic:
    """مبحث استخراج‌شده از فایل کتاب."""

    title: str
    questions: list["ImportedQuestion"] = field(default_factory=list)


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
    resource_type: str = "book_test"
    chapters: list[ImportedChapter] = field(default_factory=list)

    @property
    def question_count(self) -> int:
        return sum(len(t.questions) for ch in self.chapters for t in ch.topics)


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
            if not isinstance(tp_raw, dict):
                raise ValidationError(f"مبحث شماره {ti + 1} فصل «{ch_title}» باید یک شیء JSON باشد.")
            tp_title = _clean(tp_raw.get("title"))
            if not tp_title:
                raise ValidationError(f"عنوان مبحث شماره {ti + 1} فصل «{ch_title}» الزامی است.")
            topic = ImportedTopic(title=tp_title)
            questions_raw = tp_raw.get("questions", [])
            if not isinstance(questions_raw, list) or not questions_raw:
                raise ValidationError(f"مبحث «{tp_title}» باید حداقل یک سوال داشته باشد.")
            for q_raw in questions_raw:
                if not isinstance(q_raw, dict):
                    raise ValidationError(f"سوال در مبحث «{tp_title}» باید یک شیء JSON باشد.")
                number = _clean(q_raw.get("number"))
                if not number:
                    raise ValidationError(f"شماره سوال در مبحث «{tp_title}» الزامی است.")
                key = (tp_title, number)
                if key in seen_numbers:
                    raise ValidationError(f"شماره سوال «{number}» در مبحث «{tp_title}» تکراری است.")
                seen_numbers.add(key)
                tags_raw = q_raw.get("tags", [])
                if not isinstance(tags_raw, list):
                    tags_raw = [str(tags_raw)]
                topic.questions.append(ImportedQuestion(
                    number=number,
                    correct_answer=normalize_answer(q_raw.get("answer", q_raw.get("correct_answer"))),
                    difficulty=normalize_difficulty(q_raw.get("difficulty")),
                    importance=parse_importance(q_raw.get("importance")),
                    tags=[str(t) for t in tags_raw],
                    text=_clean(q_raw.get("text")) or None,
                ))
            chapter.topics.append(topic)
        book.chapters.append(chapter)

    if book.question_count == 0:
        raise ValidationError("کتاب باید حداقل یک سوال داشته باشد.")
    return book
