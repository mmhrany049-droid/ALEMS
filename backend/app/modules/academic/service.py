"""سرویس دانش آموزشی — درخت دروس، منابع، وارد کردن کتاب، بانک سوال."""
from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.academic.domain import ImportedBook, ImportedChapter, ImportedTopic, parse_book_json
from app.modules.academic.models import Chapter, Question, Resource, Subject, Topic
from app.shared.exceptions import NotFoundError, ValidationError


# ---------- درخت دروس ----------

def list_subjects(db: Session, field: str | None = None, grade: str | None = None) -> list[Subject]:
    stmt = select(Subject).order_by(Subject.field, Subject.grade, Subject.order_index)
    if field:
        stmt = stmt.where(Subject.field == field)
    if grade:
        stmt = stmt.where(Subject.grade == grade)
    return list(db.scalars(stmt))


def get_subject(db: Session, subject_id: uuid.UUID) -> Subject:
    subject = db.get(Subject, subject_id)
    if subject is None:
        raise NotFoundError("درس مورد نظر یافت نشد.")
    return subject


def list_chapters(db: Session, subject_id: uuid.UUID) -> list[Chapter]:
    get_subject(db, subject_id)  # اطمینان از وجود
    return list(db.scalars(
        select(Chapter).where(Chapter.subject_id == subject_id).order_by(Chapter.order_index)
    ))


def get_chapter(db: Session, chapter_id: uuid.UUID) -> Chapter:
    chapter = db.get(Chapter, chapter_id)
    if chapter is None:
        raise NotFoundError("فصل مورد نظر یافت نشد.")
    return chapter


def list_topics(db: Session, chapter_id: uuid.UUID) -> list[Topic]:
    get_chapter(db, chapter_id)
    return list(db.scalars(
        select(Topic).where(Topic.chapter_id == chapter_id).order_by(Topic.order_index)
    ))


def get_topic(db: Session, topic_id: uuid.UUID) -> Topic:
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise NotFoundError("مبحث مورد نظر یافت نشد.")
    return topic


# ---------- منابع ----------

def list_resources(db: Session, subject_id: uuid.UUID | None = None,
                   type_: str | None = None) -> list[Resource]:
    stmt = select(Resource).order_by(Resource.created_at.desc())
    if subject_id:
        stmt = stmt.where(Resource.subject_id == subject_id)
    if type_:
        stmt = stmt.where(Resource.type == type_)
    return list(db.scalars(stmt))


def get_resource(db: Session, resource_id: uuid.UUID) -> Resource:
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise NotFoundError("منبع مورد نظر یافت نشد.")
    return resource


def find_resource(db: Session, title: str, publisher: str | None) -> Resource | None:
    """یافتن کتاب تکراری بر اساس عنوان + ناشر (قانون ۸.۵)."""
    stmt = select(Resource).where(Resource.title == title)
    if publisher:
        stmt = stmt.where(Resource.publisher == publisher)
    return db.scalar(stmt.order_by(Resource.created_at.desc()))


def list_questions(
    db: Session,
    resource_id: uuid.UUID,
    topic_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Question], int]:
    """سوالات یک منبع با صفحه‌بندی."""
    get_resource(db, resource_id)
    stmt = select(Question).where(Question.resource_id == resource_id)
    count_stmt = select(func.count()).select_from(Question).where(Question.resource_id == resource_id)
    if topic_id:
        stmt = stmt.where(Question.topic_id == topic_id)
        count_stmt = count_stmt.where(Question.topic_id == topic_id)
    total = db.scalar(count_stmt) or 0
    rows = list(db.scalars(
        stmt.options(selectinload(Question.topic))
        .order_by(Question.topic_id, Question.number)
        .offset(offset).limit(limit)
    ))
    return rows, int(total)


def get_question(db: Session, question_id: uuid.UUID) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise NotFoundError("سوال مورد نظر یافت نشد.")
    return question


def get_questions_bulk(db: Session, question_ids: list[uuid.UUID]) -> list[Question]:
    rows = list(db.scalars(select(Question).where(Question.id.in_(question_ids))))
    found = {q.id for q in rows}
    missing = set(question_ids) - found
    if missing:
        raise NotFoundError(f"{len(missing)} سوال از سوالات انتخاب‌شده یافت نشد.")
    return rows


# ---------- وارد کردن کتاب ----------

def import_book(db: Session, data: dict, *, update_existing: bool = False) -> dict:
    """وارد کردن کتاب تست از JSON (AT-07/AT-08).

    قانون ۸.۵: در صورت تکراری بودن (عنوان + ناشر)، بدون «update_existing» خطای تعارض
    با گزینه به‌روزرسانی برمی‌گردد؛ سوالات بدون مبحث معتبر وارد نمی‌شوند.
    """
    book = parse_book_json(data)

    existing = find_resource(db, book.title, book.publisher)
    if existing is not None and not update_existing:
        raise ValidationError(
            f"کتابی با عنوان «{book.title}» و همین ناشر قبلاً وارد شده است.",
            details={"duplicate": True, "resource_id": str(existing.id),
                     "options": ["update_existing=true برای به‌روزرسانی"]},
        )

    if existing is not None and update_existing:
        resource = existing
        _delete_book_content(db, resource)
    else:
        resource = Resource(title=book.title, type=book.resource_type, publisher=book.publisher)

    subject: Subject | None = None
    if book.subject_name:
        subject = db.scalar(select(Subject).where(Subject.name == book.subject_name).limit(1))
    resource.subject_id = subject.id if subject else resource.subject_id
    resource.resource_metadata = {
        "imported_question_count": book.question_count,
        "chapter_count": len(book.chapters),
    }
    db.add(resource)
    db.flush()

    for chapter_data in book.chapters:
        chapter = Chapter(subject_id=resource.subject_id or _fallback_subject(db).id,
                          title=chapter_data.title, order_index=int(chapter_data.order_index or 0))
        db.add(chapter)
        db.flush()
        for topic_data in chapter_data.topics:
            topic = Topic(chapter_id=chapter.id, title=topic_data.title,
                          order_index=len(chapter.topics))
            db.add(topic)
            db.flush()
            for q in topic_data.questions:
                db.add(Question(
                    resource_id=resource.id,
                    topic_id=topic.id,
                    number=q.number,
                    correct_answer=q.correct_answer,
                    difficulty=q.difficulty,
                    importance=q.importance,
                    tags=q.tags,
                    text=q.text,
                ))
    db.commit()
    db.refresh(resource)
    return {
        "resource_id": str(resource.id),
        "title": resource.title,
        "chapters": len(book.chapters),
        "topics": sum(len(ch.topics) for ch in book.chapters),
        "questions": book.question_count,
        "updated": existing is not None,
        "subject_matched": subject.name if subject else None,
    }


def _fallback_subject(db: Session) -> Subject:
    """درس عمومی برای کتاب‌هایی که درس مشخصی ندارند."""
    subject = db.scalar(select(Subject).where(Subject.name == "عمومی").limit(1))
    if subject is None:
        subject = Subject(name="عمومی", field="ریاضی", grade="دهم", order_index=999)
        db.add(subject)
        db.flush()
    return subject


def _delete_book_content(db: Session, resource: Resource) -> None:
    """حذف سوالات قدیمی کتاب هنگام به‌روزرسانی."""
    for question in list(db.scalars(select(Question).where(Question.resource_id == resource.id))):
        db.delete(question)


# ---------- پیلودهای خروجی ----------

def subject_payload(subject: Subject) -> dict:
    return {"id": str(subject.id), "name": subject.name, "field": subject.field,
            "grade": subject.grade, "order_index": subject.order_index}


def chapter_payload(chapter: Chapter) -> dict:
    return {"id": str(chapter.id), "subject_id": str(chapter.subject_id),
            "title": chapter.title, "order_index": chapter.order_index}


def topic_payload(topic: Topic) -> dict:
    return {"id": str(topic.id), "chapter_id": str(topic.chapter_id),
            "title": topic.title, "parent_id": str(topic.parent_id) if topic.parent_id else None,
            "order_index": topic.order_index}


def resource_payload(resource: Resource, question_count: int | None = None) -> dict:
    data = {
        "id": str(resource.id),
        "title": resource.title,
        "type": resource.type,
        "subject_id": str(resource.subject_id) if resource.subject_id else None,
        "publisher": resource.publisher,
        "metadata": resource.resource_metadata or {},
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }
    if question_count is not None:
        data["question_count"] = question_count
    return data


def question_payload(question: Question) -> dict:
    topic = question.topic
    chapter = topic.chapter if topic else None
    subject = chapter.subject if chapter else None
    return {
        "id": str(question.id),
        "resource_id": str(question.resource_id),
        "topic_id": str(question.topic_id),
        "topic_title": topic.title if topic else None,
        "chapter_title": chapter.title if chapter else None,
        "subject_name": subject.name if subject else None,
        "number": question.number,
        "difficulty": question.difficulty,
        "importance": question.importance,
        "tags": question.tags or [],
        "text": question.text,
    }
