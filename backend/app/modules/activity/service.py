"""سرویس فعالیت — ثبت فعالیت، رکورد تست، تیک‌ها، دفترچه خطا، صف مرور."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.events import event_bus
from app.modules.activity.domain import MARK_TO_REASON, ReviewPolicy, compute_queue_plans, validate_error_type
from app.modules.activity.models import (
    ErrorNote,
    LearningActivity,
    QuestionMark,
    ReviewItem,
    TestRecord,
)
from app.modules.academic.models import Chapter, Question, Subject, Topic
from app.modules.academic.service import get_questions_bulk
from app.modules.settings.service import get_review_policy
from app.shared.exceptions import NotFoundError, ValidationError


# ---------- فعالیت ----------

def create_activity(db: Session, student_id: uuid.UUID, data: dict) -> LearningActivity:
    activity = LearningActivity(student_id=student_id, **data)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def list_activities(
    db: Session, student_id: uuid.UUID, from_dt: datetime | None = None,
    to_dt: datetime | None = None, type_: str | None = None,
    limit: int = 50, offset: int = 0,
) -> tuple[list[LearningActivity], int]:
    stmt = select(LearningActivity).where(LearningActivity.student_id == student_id)
    count_stmt = select(func.count()).select_from(LearningActivity).where(
        LearningActivity.student_id == student_id
    )
    if from_dt:
        stmt = stmt.where(LearningActivity.started_at >= from_dt)
        count_stmt = count_stmt.where(LearningActivity.started_at >= from_dt)
    if to_dt:
        stmt = stmt.where(LearningActivity.started_at <= to_dt)
        count_stmt = count_stmt.where(LearningActivity.started_at <= to_dt)
    if type_:
        stmt = stmt.where(LearningActivity.type == type_)
        count_stmt = count_stmt.where(LearningActivity.type == type_)
    total = db.scalar(count_stmt) or 0
    rows = list(db.scalars(
        stmt.order_by(LearningActivity.started_at.desc()).offset(offset).limit(limit)
    ))
    return rows, int(total)


def delete_activity(db: Session, student_id: uuid.UUID, activity_id: uuid.UUID) -> None:
    activity = db.get(LearningActivity, activity_id)
    if activity is None or activity.student_id != student_id:
        raise NotFoundError("فعالیت مورد نظر یافت نشد.")
    db.delete(activity)
    db.commit()


# ---------- رکورد تست ----------

def create_test_records(db: Session, student_id: uuid.UUID, items: list[dict]) -> list[TestRecord]:
    """ثبت دسته‌ای نتیجه سوالات + تیک‌ها + دفترچه خطا (AT-10/AT-11).

    پس از ثبت، رویداد «test_records.created» اعلام می‌شود تا صف مرور به‌روز شود.
    """
    question_ids = [item["question_id"] for item in items]
    questions = {q.id: q for q in get_questions_bulk(db, question_ids)}

    records: list[TestRecord] = []
    for item in items:
        question = questions[item["question_id"]]
        error_type = validate_error_type(item.get("error_type"), item["result"])
        record = TestRecord(
            student_id=student_id,
            question_id=question.id,
            result=item["result"],
            solved_at=item.get("solved_at") or datetime.utcnow(),
            duration_seconds=item.get("duration_seconds"),
        )
        db.add(record)
        db.flush()
        if error_type is not None:
            db.add(ErrorNote(test_record_id=record.id, error_type=error_type,
                             note=item.get("error_note")))
        for mark in item.get("marks", []):
            _upsert_mark(db, student_id, question.id, mark)
        records.append(record)

    db.commit()
    for record in records:
        db.refresh(record)
    event_bus.emit("test_records.created", {"student_id": str(student_id), "count": len(records)})
    return records


def _upsert_mark(db: Session, student_id: uuid.UUID, question_id: uuid.UUID, mark_type: str) -> None:
    existing = db.scalar(select(QuestionMark).where(
        QuestionMark.student_id == student_id,
        QuestionMark.question_id == question_id,
        QuestionMark.mark_type == mark_type,
    ))
    if existing is None:
        db.add(QuestionMark(student_id=student_id, question_id=question_id, mark_type=mark_type))


def list_test_records(
    db: Session, student_id: uuid.UUID, from_date: date | None, to_date: date | None,
    subject_id: uuid.UUID | None, limit: int = 50, offset: int = 0,
) -> tuple[list[TestRecord], int]:
    stmt = select(TestRecord).where(TestRecord.student_id == student_id)
    count_stmt = select(func.count()).select_from(TestRecord).where(TestRecord.student_id == student_id)
    if from_date:
        stmt = stmt.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
        count_stmt = count_stmt.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        end_dt = datetime.combine(to_date, datetime.max.time())
        stmt = stmt.where(TestRecord.solved_at <= end_dt)
        count_stmt = count_stmt.where(TestRecord.solved_at <= end_dt)
    if subject_id:
        stmt = stmt.join(Question, TestRecord.question_id == Question.id).where(
            Question.topic_id.in_(select(Topic.id).where(
                Topic.chapter_id.in_(select(Chapter.id).where(Chapter.subject_id == subject_id))
            ))
        )
        count_stmt = count_stmt.join(Question, TestRecord.question_id == Question.id).where(
            Question.topic_id.in_(select(Topic.id).where(
                Topic.chapter_id.in_(select(Chapter.id).where(Chapter.subject_id == subject_id))
            ))
        )
    total = db.scalar(count_stmt) or 0
    rows = list(db.scalars(
        stmt.options(selectinload(TestRecord.question), selectinload(TestRecord.error_note))
        .order_by(TestRecord.solved_at.desc())
        .offset(offset).limit(limit)
    ))
    return rows, int(total)


# ---------- تیک‌ها ----------

def add_mark(db: Session, student_id: uuid.UUID, question_id: uuid.UUID, mark_type: str) -> QuestionMark:
    """افزودن تیک — تیک‌ها مستقل از نتیجه تست هستند (قانون ۸.۳) (AT-12)."""
    if db.get(Question, question_id) is None:
        raise NotFoundError("سوال مورد نظر یافت نشد.")
    _upsert_mark(db, student_id, question_id, mark_type)
    db.commit()
    return db.scalar(select(QuestionMark).where(
        QuestionMark.student_id == student_id,
        QuestionMark.question_id == question_id,
        QuestionMark.mark_type == mark_type,
    ))


def remove_mark(db: Session, student_id: uuid.UUID, question_id: uuid.UUID, mark_type: str) -> None:
    row = db.scalar(select(QuestionMark).where(
        QuestionMark.student_id == student_id,
        QuestionMark.question_id == question_id,
        QuestionMark.mark_type == mark_type,
    ))
    if row is None:
        raise NotFoundError("این تیک روی سوال ثبت نشده است.")
    db.delete(row)
    db.commit()


def get_marks_map(db: Session, student_id: uuid.UUID) -> dict[str, list[str]]:
    rows = db.scalars(select(QuestionMark).where(QuestionMark.student_id == student_id))
    result: dict[str, list[str]] = {}
    for row in rows:
        result.setdefault(str(row.question_id), []).append(row.mark_type)
    return result


# ---------- صف مرور ----------

def rebuild_review_queue(db: Session, student_id: uuid.UUID) -> dict:
    """بازسازی صف مرور بر اساس قوانین (AT-13).

    - غلط‌ها و (در صورت تنظیم) نزده‌ها + تیک‌های مرور/مهم/سخت وارد صف می‌شوند.
    - آیتم‌های pending موجود حفظ می‌شوند؛ موارد جدید اضافه می‌شوند.
    - آیتم‌های pending که دیگر واجد شرایط نیستند حذف می‌شوند.
    - آیتم‌های done فقط اگر مرور بعدی‌شان سررسید شده دوباره اضافه می‌شوند.
    """
    policy = get_review_policy(db)
    today = date.today()

    # آخرین نتیجه هر سوال (قانون ۸.۳: آخرین نتیجه وضعیت جاری است)
    latest_subq = (
        select(TestRecord.question_id, func.max(TestRecord.solved_at).label("max_solved"))
        .where(TestRecord.student_id == student_id)
        .group_by(TestRecord.question_id)
        .subquery()
    )
    latest_results = db.execute(
        select(TestRecord.question_id, TestRecord.result)
        .join(latest_subq, (TestRecord.question_id == latest_subq.c.question_id)
              & (TestRecord.solved_at == latest_subq.c.max_solved))
        .where(TestRecord.student_id == student_id)
    ).all()
    wrong_ids = [str(qid) for qid, result in latest_results if result == "wrong"]
    blank_ids = [str(qid) for qid, result in latest_results if result == "blank"]

    marks_map = get_marks_map(db, student_id)
    marked_relevant = {
        qid: [m for m in marks if m in MARK_TO_REASON]
        for qid, marks in marks_map.items()
        if any(m in MARK_TO_REASON for m in marks)
    }

    plans = compute_queue_plans(
        wrong_question_ids=wrong_ids,
        blank_question_ids=blank_ids,
        marked_question_ids=marked_relevant,
        policy=policy,
        today=today,
    )

    existing_pending = {
        str(item.question_id): item
        for item in db.scalars(select(ReviewItem).where(
            ReviewItem.student_id == student_id, ReviewItem.status == "pending"
        ))
    }

    added = 0
    for qid, plan in plans.items():
        if qid in existing_pending:
            item = existing_pending[qid]
            item.reason = plan.reasons[0]
            item.priority = max(item.priority, plan.priority)
        else:
            db.add(ReviewItem(
                student_id=student_id,
                question_id=uuid.UUID(qid),
                reason=plan.reasons[0],
                priority=plan.priority,
                scheduled_date=plan.scheduled_date,
            ))
            added += 1

    removed = 0
    for qid, item in existing_pending.items():
        if qid not in plans:
            db.delete(item)
            removed += 1

    db.commit()
    return {"added": added, "removed": removed, "pending": len(plans)}


def list_review_queue(
    db: Session, student_id: uuid.UUID, from_date: date | None = None,
    to_date: date | None = None, status: str = "pending",
) -> list[ReviewItem]:
    """لیست صف مرور — مرتب بر اساس اولویت و تاریخ (بالا به پایین)."""
    stmt = select(ReviewItem).where(
        ReviewItem.student_id == student_id, ReviewItem.status == status
    )
    if from_date:
        stmt = stmt.where(ReviewItem.scheduled_date >= from_date)
    if to_date:
        stmt = stmt.where(ReviewItem.scheduled_date <= to_date)
    return list(db.scalars(
        stmt.options(selectinload(ReviewItem.question).selectinload(Question.topic))
        .order_by(ReviewItem.priority.desc(), ReviewItem.scheduled_date.asc())
    ))


def complete_review(db: Session, student_id: uuid.UUID, item_id: uuid.UUID) -> ReviewItem:
    """علامت‌گذاری «مرور شد» + پیشنهاد تاریخ مرور بعدی با چرخه ۱-۳-۷-۱۴ (AT-14)."""
    item = db.get(ReviewItem, item_id)
    if item is None or item.student_id != student_id:
        raise NotFoundError("آیتم مرور مورد نظر یافت نشد.")
    if item.status == "done":
        raise ValidationError("این آیتم قبلاً مرور شده است.")
    item.status = "done"
    item.reviewed_at = datetime.utcnow()
    item.review_count += 1
    policy = get_review_policy(db)
    item.scheduled_date = policy.next_review_date(item.review_count, date.today())
    db.commit()
    db.refresh(item)
    return item


def reopen_review(db: Session, student_id: uuid.UUID, item_id: uuid.UUID) -> ReviewItem:
    """بازگرداندن سوال به صف (قانون ۸.۲ بند ۵)."""
    item = db.get(ReviewItem, item_id)
    if item is None or item.student_id != student_id:
        raise NotFoundError("آیتم مرور مورد نظر یافت نشد.")
    item.status = "pending"
    item.reviewed_at = None
    item.scheduled_date = date.today()
    db.commit()
    db.refresh(item)
    return item


# ---------- پیلودها ----------

def activity_payload(activity: LearningActivity, subject_name: str | None = None) -> dict:
    return {
        "id": str(activity.id),
        "type": activity.type,
        "subject_id": str(activity.subject_id) if activity.subject_id else None,
        "resource_id": str(activity.resource_id) if activity.resource_id else None,
        "started_at": activity.started_at.isoformat(),
        "duration_minutes": activity.duration_minutes,
        "note": activity.note,
        "subject_name": subject_name,
    }


def test_record_payload(record: TestRecord) -> dict:
    question = record.question
    topic = question.topic if question else None
    return {
        "id": str(record.id),
        "question_id": str(record.question_id),
        "result": record.result,
        "solved_at": record.solved_at.isoformat(),
        "duration_seconds": record.duration_seconds,
        "question_number": question.number if question else None,
        "topic_title": topic.title if topic else None,
        "error_type": record.error_note.error_type if record.error_note else None,
        "error_note": record.error_note.note if record.error_note else None,
    }


def review_item_payload(item: ReviewItem, marks: list[str] | None = None) -> dict:
    question = item.question
    topic = question.topic if question else None
    return {
        "id": str(item.id),
        "question_id": str(item.question_id),
        "reason": item.reason,
        "priority": item.priority,
        "scheduled_date": item.scheduled_date.isoformat(),
        "status": item.status,
        "review_count": item.review_count,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "question_number": question.number if question else None,
        "topic_title": topic.title if topic else None,
        "difficulty": question.difficulty if question else None,
        "marks": marks or [],
    }
