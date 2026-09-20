"""Academic Knowledge (Books & Import) — pure domain rules, NO I/O (doc 03 §3.1).

doc 08 §8.3 (Import کتاب) + doc 09 §9.1:
1. questions غایب یا [] → مجاز (TOC-only) — هیچ قاعده «حداقل یک سوال» وجود ندارد
2. اگر question هست → number و answer الزامی
3. topic بدون سوال مستقیم و فقط با subtopics → مجاز
4. block_type پیش‌فرض topic؛ از روی عنوان («کنکور»، «آزمون»/«جامع»، «چکاپ»، «مخلوط») قابل استنتاج
5. کتاب تکراری (title+publisher) → 409 با گزینه به‌روزرسانی (در service)

doc 05: block_type ∈ topic|mixed|chapter_exam|checkup|konkur|other
"""
from __future__ import annotations

BLOCK_TYPES = ("topic", "mixed", "chapter_exam", "checkup", "konkur", "other")

# Persian labels for block types (UI badges + import schema endpoint)
BLOCK_TYPE_LABELS_FA = {
    "topic": "مبحث",
    "mixed": "ترکیبی",
    "chapter_exam": "آزمون فصل",
    "checkup": "چکاپ",
    "konkur": "کنکور",
    "other": "سایر",
}

# نیم‌فاصله (ZWNJ) عمداً حفظ می‌شود — «دوره‌ای» همان‌طور که کاربر نوشته ذخیره/نمایش داده می‌شود
_ARABIC_TO_PERSIAN = str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "\xa0": " "})


def normalize_text(value: str | None) -> str:
    """Trim + unify Arabic/Persian glyphs + collapse spaces (stable uniqueness keys)."""
    if not value:
        return ""
    return " ".join(value.translate(_ARABIC_TO_PERSIAN).split())


def infer_block_type(title: str) -> str:
    """doc 09 §9.1 — استنتاج block_type از عنوان (اگر در فایل نیامده باشد).

    - شامل «کنکور» → konkur
    - شامل «جامع» یا «آزمون» (مثل [آزمون] / آزمون فصل) → chapter_exam
    - شامل «چکاپ» → checkup
    - شامل «مخلوط» → mixed
    - وگرنه → topic
    """
    t = normalize_text(title)
    if "کنکور" in t:
        return "konkur"
    if "جامع" in t or "آزمون" in t:
        return "chapter_exam"
    if "چکاپ" in t:
        return "checkup"
    if "مخلوط" in t:
        return "mixed"
    return "topic"


def _validate_questions(questions: list[dict], where: str, errors: list[str]) -> None:
    """doc 08 §8.3.2 — اگر question هست: number و answer الزامی.

    سوال‌ها می‌توانند غایب یا [] باشند (TOC-only) — آن حالت اصلاً اینجا خطا نمی‌گیرد.
    """
    for idx, q in enumerate(questions, start=1):
        if q.get("number") is None:
            errors.append(f"{where}: سوال {idx} — شماره (number) الزامی است.")
        answer = q.get("answer")
        if answer is None or str(answer).strip() == "":
            errors.append(f"{where}: سوال {idx} — پاسخ (answer) الزامی است.")
        for field, label in (("difficulty", "سختی"), ("importance", "اهمیت")):
            v = q.get(field)
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 5)):
                errors.append(f"{where}: سوال {idx} — {label} باید عددی بین ۱ تا ۵ باشد.")


def _validate_topic(topic: dict, where: str, errors: list[str]) -> None:
    title = normalize_text(topic.get("title"))
    here = f"{where} → «{title}»" if title else where
    if not title:
        errors.append(f"{where}: عنوان موضوع الزامی است.")
    _validate_questions(topic.get("questions") or [], here, errors)
    for sub in topic.get("subtopics") or []:
        _validate_topic(sub, f"{here} → زیرمبحث", errors)


def validate_book_payload(data: dict) -> list[str]:
    """Return Persian error list (empty when valid).

    TOC-only کاملاً معتبر است: chapters بدون هیچ question، topic فقط با
    subtopics، و حتی کتاب بدون chapter → موفقیت (doc 08 §8.3).
    """
    errors: list[str] = []
    if not normalize_text(data.get("title")):
        errors.append("عنوان کتاب الزامی است.")

    for ci, chapter in enumerate(data.get("chapters") or [], start=1):
        ctitle = normalize_text(chapter.get("title"))
        if not ctitle:
            errors.append(f"فصل {ci}: عنوان فصل الزامی است.")
        where = f"فصل «{ctitle or ci}»"
        _validate_questions(chapter.get("questions") or [], where, errors)
        for topic in list(chapter.get("topics") or []) + list(chapter.get("subtopics") or []):
            _validate_topic(topic, where, errors)

    for ti, topic in enumerate(data.get("topics") or [], start=1):
        _validate_topic(topic, f"موضوع {ti} (بدون فصل)", errors)

    return errors


def count_payload(data: dict) -> dict[str, int]:
    """Preview counters for the import payload (chapters/topics/questions)."""
    chapters = 0
    topics = 0
    questions = 0

    def walk_topic(t: dict) -> None:
        nonlocal topics, questions
        topics += 1
        questions += len(t.get("questions") or [])
        for sub in t.get("subtopics") or []:
            walk_topic(sub)

    for ch in data.get("chapters") or []:
        chapters += 1
        questions += len(ch.get("questions") or [])
        for t in list(ch.get("topics") or []) + list(ch.get("subtopics") or []):
            walk_topic(t)
    for t in data.get("topics") or []:
        walk_topic(t)
    return {"chapters": chapters, "topics": topics, "questions": questions}


def taught_state(own_and_descendant_flags: list[bool]) -> str:
    """doc 08 §8.8 — parent می‌تواند indeterminate باشد: 'all' | 'none' | 'partial'."""
    flags = own_and_descendant_flags
    if not flags:
        return "none"
    if all(flags):
        return "all"
    if not any(flags):
        return "none"
    return "partial"
