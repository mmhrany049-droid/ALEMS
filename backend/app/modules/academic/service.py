"""Academic Knowledge (Books & Import) — application services (doc 06 §Books & Import).

- POST /resources/import-book  → TOC-only مجاز (doc 08 §8.3.1) — هیچ «حداقل یک سوال» وجود ندارد
- GET  /resources/import-book/schema
- GET  /resources
- GET  /resources/{id}/tree
- children_map_for: نقشه parent→children برای cascade taught (doc 08 §8.8) —
  توسط student.service در PUT /students/me/taught-topics استفاده می‌شود.
"""
from __future__ import annotations

from collections import defaultdict

from fastapi.exceptions import HTTPException
from sqlalchemy import delete, func, select

from app.modules.academic import domain
from app.modules.academic.models import AnswerKey, Question, Resource, Topic
from app.modules.student.models import Student, TaughtTopic

MSG_BOOK_NOT_FOUND = "کتاب پیدا نشد."


# --- import ------------------------------------------------------------------

def _duplicate_msg(title: str, publisher: str) -> str:
    pub = f" از نشر «{publisher}»" if publisher else ""
    return f"کتاب «{title}»{pub} قبلاً وارد شده است. برای به‌روزرسانی، گزینه جایگزینی را انتخاب کن."


def _import_questions(db, topic_row: Topic, questions: list) -> None:
    for q in questions:
        qrow = Question(
            topic_id=topic_row.id,
            number=q.number,
            difficulty=q.difficulty,
            importance=q.importance,
            tags=list(q.tags or []),
        )
        db.add(qrow)
        db.flush()
        # doc 05 — کلید نسخه‌دار؛ نسخه ۱ در import (تاریخچه در فاز ۳+)
        db.add(AnswerKey(question_id=qrow.id, answer=str(q.answer).strip(), version=1))


def _import_topic(db, resource_id: str, t, parent_id: str | None, order: int) -> Topic:
    title = domain.normalize_text(t.title)
    block_type = t.block_type or domain.infer_block_type(title)
    children = list(t.subtopics or [])
    # doc 05 — is_structural: گره فقط‌ساختار (فرزند دارد ولی سوال مستقیم ندارد)
    structural = bool(children) and not (t.questions or [])
    row = Topic(
        resource_id=resource_id,
        parent_id=parent_id,
        title=title,
        block_type=block_type,
        is_structural=structural,
        sort_order=order,
    )
    db.add(row)
    db.flush()
    _import_questions(db, row, t.questions or [])
    for j, sub in enumerate(children):
        _import_topic(db, resource_id, sub, parent_id=row.id, order=j)
    return row


def _import_chapter(db, resource_id: str, ch, order: int) -> Topic:
    title = domain.normalize_text(ch.title)
    block_type = ch.block_type or domain.infer_block_type(title)
    row = Topic(
        resource_id=resource_id,
        parent_id=None,
        title=title,
        block_type=block_type,
        is_structural=True,  # فصل = گره ساختاری (doc 05)
        sort_order=order,
    )
    db.add(row)
    db.flush()
    _import_questions(db, row, ch.questions or [])
    children = list(ch.topics or []) + list(ch.subtopics or [])
    for j, t in enumerate(children):
        _import_topic(db, resource_id, t, parent_id=row.id, order=j)
    return row


def _replace_existing(db, student: Student, existing: Resource) -> None:
    """Delete old book (FK cascade: topics→questions→answer_keys) + taught rows."""
    topic_ids = db.execute(select(Topic.id).where(Topic.resource_id == existing.id)).scalars().all()
    if topic_ids:
        db.execute(
            delete(TaughtTopic).where(
                TaughtTopic.student_id == student.id, TaughtTopic.topic_id.in_(topic_ids)
            )
        )
    db.delete(existing)
    db.flush()


def import_book(db, student: Student, payload) -> dict:
    errors = domain.validate_book_payload(payload.model_dump())
    if errors:
        raise HTTPException(status_code=422, detail=errors[0])

    title = domain.normalize_text(payload.title)
    publisher = domain.normalize_text(payload.publisher)
    subject = domain.normalize_text(payload.subject) or None

    existing = db.execute(
        select(Resource).where(
            Resource.student_id == student.id,
            Resource.title == title,
            Resource.publisher == publisher,
        )
    ).scalar_one_or_none()

    replaced = False
    if existing is not None:
        if not payload.replace:
            # doc 08 §8.3.5 — duplicate (title+publisher) → 409 با گزینه به‌روزرسانی
            raise HTTPException(status_code=409, detail=_duplicate_msg(title, publisher))
        _replace_existing(db, student, existing)
        replaced = True

    resource = Resource(student_id=student.id, title=title, publisher=publisher, subject=subject)
    db.add(resource)
    db.flush()

    chapters = list(payload.chapters or [])
    for i, ch in enumerate(chapters):
        _import_chapter(db, resource.id, ch, order=i)
    for i, t in enumerate(payload.topics or []):
        _import_topic(db, resource.id, t, parent_id=None, order=len(chapters) + i)
    db.flush()

    return {"resource": _resource_out(db, resource), "replaced": replaced}


# --- read --------------------------------------------------------------------

def _counts_for(db, resource_ids: list[str]) -> dict[str, dict[str, int]]:
    """chapters = فصل‌های ریشه (structural root) · topics = بقیه گره‌ها · questions = کل سوال‌ها."""
    counts: dict[str, dict[str, int]] = {
        rid: {"chapters": 0, "topics": 0, "questions": 0} for rid in resource_ids
    }
    if not resource_ids:
        return counts
    rows = db.execute(
        select(Topic.resource_id, func.count())
        .where(Topic.resource_id.in_(resource_ids), Topic.is_structural.is_(True), Topic.parent_id.is_(None))
        .group_by(Topic.resource_id)
    ).all()
    for rid, n in rows:
        counts[rid]["chapters"] = int(n)
    rows = db.execute(
        select(Topic.resource_id, func.count())
        .where(Topic.resource_id.in_(resource_ids))
        .group_by(Topic.resource_id)
    ).all()
    for rid, n in rows:
        counts[rid]["topics"] = int(n) - counts[rid]["chapters"]
    rows = db.execute(
        select(Topic.resource_id, func.count(Question.id))
        .join(Question, Question.topic_id == Topic.id)
        .where(Topic.resource_id.in_(resource_ids))
        .group_by(Topic.resource_id)
    ).all()
    for rid, n in rows:
        counts[rid]["questions"] = int(n)
    return counts


def _resource_out(db, resource: Resource) -> dict:
    counts = _counts_for(db, [resource.id])[resource.id]
    return {
        "id": resource.id,
        "title": resource.title,
        "publisher": resource.publisher,
        "subject": resource.subject,
        "counts": counts,
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }


def list_resources(db, student: Student) -> list[dict]:
    resources = (
        db.execute(
            select(Resource)
            .where(Resource.student_id == student.id)
            .order_by(Resource.created_at.desc())
        )
        .scalars()
        .all()
    )
    counts = _counts_for(db, [r.id for r in resources])
    return [
        {
            "id": r.id,
            "title": r.title,
            "publisher": r.publisher,
            "subject": r.subject,
            "counts": counts[r.id],
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in resources
    ]


def get_tree(db, student: Student, resource_id: str) -> dict:
    resource = db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.student_id == student.id)
    ).scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=404, detail=MSG_BOOK_NOT_FOUND)

    rows = (
        db.execute(
            select(Topic).where(Topic.resource_id == resource.id).order_by(Topic.sort_order, Topic.id)
        )
        .scalars()
        .all()
    )
    qcounts = dict(
        db.execute(
            select(Question.topic_id, func.count())
            .join(Topic, Topic.id == Question.topic_id)
            .where(Topic.resource_id == resource.id)
            .group_by(Question.topic_id)
        ).all()
    )
    taught_map = dict(
        db.execute(
            select(TaughtTopic.topic_id, TaughtTopic.taught).where(
                TaughtTopic.student_id == student.id,
                TaughtTopic.topic_id.in_([t.id for t in rows] or ["-"]),
            )
        ).all()
    )

    by_parent: dict[str | None, list[Topic]] = defaultdict(list)
    for t in rows:
        by_parent[t.parent_id].append(t)

    def build(t: Topic) -> tuple[dict, list[bool]]:
        children_nodes = []
        flags: list[bool] = []
        for child in by_parent.get(t.id, []):
            node, child_flags = build(child)
            children_nodes.append(node)
            flags.extend(child_flags)
        own = bool(taught_map.get(t.id, False))
        all_flags = [own, *flags]
        node = {
            "id": t.id,
            "title": t.title,
            "block_type": t.block_type,
            "block_type_fa": domain.BLOCK_TYPE_LABELS_FA.get(t.block_type, t.block_type),
            "is_structural": t.is_structural,
            "question_count": int(qcounts.get(t.id, 0)),
            "taught": own,
            "taught_state": domain.taught_state(all_flags),
            "children": children_nodes,
        }
        return node, all_flags

    tree = [build(root)[0] for root in by_parent.get(None, [])]
    return {"resource": _resource_out(db, resource), "tree": tree}


# --- taught cascade support (doc 08 §8.8) -------------------------------------

def children_map_for(db, topic_ids: list[str]) -> dict[str, list[str]]:
    """parent_id → [child_ids] (transitive) برای topicهای داده‌شده.

    topicهای ناشناس (خارج از درخت کتاب) بدون فرزند برمی‌گردند →
    رفتار PUT taught-topics برای آن‌ها upsert ساده می‌ماند.
    """
    result: dict[str, list[str]] = {}
    frontier = {tid for tid in topic_ids if tid}
    visited: set[str] = set(frontier)
    while frontier:
        rows = db.execute(
            select(Topic.parent_id, Topic.id).where(Topic.parent_id.in_(frontier))
        ).all()
        if not rows:
            break
        next_frontier: set[str] = set()
        for pid, cid in rows:
            result.setdefault(pid, []).append(cid)
            if cid not in visited:
                next_frontier.add(cid)
        visited |= next_frontier
        frontier = next_frontier
    return result


# --- import schema (GET /resources/import-book/schema) --------------------------

def get_import_schema() -> dict:
    return {
        "description": "ساختار فایل import کتاب — TOC-only کاملاً معتبر است (بدون هیچ سوال).",
        "toc_only": True,
        "rules": [
            "questions غایب یا [] در هر سطحی → موفقیت (TOC-only).",
            "topic بدون سوال مستقیم و فقط با subtopics → موفقیت.",
            "اگر question هست → number و answer الزامی؛ difficulty/importance اختیاری (۱ تا ۵).",
            "block_type اختیاری؛ اگر نیاید از عنوان استنتاج می‌شود.",
            "کتاب تکراری (title+publisher) → خطای 409 با گزینه جایگزینی (replace=true).",
        ],
        "fields": {
            "title": {"type": "string", "required": True, "description": "عنوان کتاب"},
            "publisher": {"type": "string", "required": False, "description": "ناشر (برای یکتایی همراه عنوان)"},
            "subject": {"type": "string", "required": False, "description": "درس، مثل «شیمی»"},
            "chapters": {"type": "array", "required": False, "description": "فصل‌ها: {title, topics[], questions[]}"},
            "topics": {"type": "array", "required": False, "description": "موضوعات بدون فصل هم مجازاند"},
            "replace": {"type": "boolean", "required": False, "description": "جایگزینی کتاب تکراری (بعد از 409)"},
        },
        "topic_fields": {
            "title": {"type": "string", "required": True},
            "block_type": {"type": "string", "required": False, "enum": list(domain.BLOCK_TYPES)},
            "subtopics": {"type": "array", "required": False, "description": "بازگشتی — همین ساختار"},
            "questions": {"type": "array", "required": False, "description": "هر سوال: number + answer الزامی"},
        },
        "block_types": [
            {"value": k, "label_fa": v} for k, v in domain.BLOCK_TYPE_LABELS_FA.items()
        ],
        "block_type_inference": [
            "شامل «کنکور» → konkur",
            "شامل «جامع» یا «آزمون» → chapter_exam",
            "شامل «چکاپ» → checkup",
            "شامل «مخلوط» → mixed",
            "وگرنه → topic",
        ],
        "example": {
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
        },
        "example_with_questions": {
            "title": "ریاضی پایه",
            "publisher": "خیلی سبز",
            "chapters": [
                {
                    "title": "فصل ۱: مجموعه‌ها",
                    "topics": [
                        {
                            "title": "آزمون فصل ۱",
                            "questions": [
                                {"number": 1, "answer": "2", "difficulty": 3},
                                {"number": 2, "answer": "4"},
                            ],
                        }
                    ],
                }
            ],
        },
    }
