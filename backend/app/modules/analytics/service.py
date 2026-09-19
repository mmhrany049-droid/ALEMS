"""سرویس تحلیل — تجمیع عملکرد بر اساس درس، مبحث، سختی و نوع اشتباه."""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.academic.models import Chapter, Question, Subject, Topic
from app.modules.activity.models import ErrorNote, TestRecord
from app.modules.analytics.domain import aggregate_counts
from app.modules.settings.service import get_scoring_policy


def _base_query(db: Session, student_id: uuid.UUID, from_date: date | None,
                to_date: date | None, subject_id: uuid.UUID | None):
    """کوئری پایه رکوردهای تست با فیلترهای بازه (inclusive)."""
    stmt = select(
        TestRecord.result, Question.topic_id,
        func.count().label("cnt"),
    ).join(Question, TestRecord.question_id == Question.id).where(
        TestRecord.student_id == student_id
    )
    if from_date:
        stmt = stmt.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(TestRecord.solved_at <= datetime.combine(to_date, datetime.max.time()))
    if subject_id is not None:
        stmt = stmt.where(Question.topic_id.in_(
            select(Topic.id).where(Topic.chapter_id.in_(
                select(Chapter.id).where(Chapter.subject_id == subject_id)
            ))
        ))
    return stmt.group_by(TestRecord.result, Question.topic_id)


def _rows_to_topic_counts(db: Session, rows) -> dict[str, dict]:
    """تبدیل ردیف‌های (result, topic_id, cnt) به آمار هر مبحث."""
    counts: dict[str, dict[str, int]] = {}
    for result, topic_id, cnt in rows:
        bucket = counts.setdefault(str(topic_id), {"correct": 0, "wrong": 0, "blank": 0})
        if result in bucket:
            bucket[result] += int(cnt)
    return counts


def by_topic(db: Session, student_id: uuid.UUID, from_date: date | None,
             to_date: date | None, subject_id: uuid.UUID | None = None) -> list[dict]:
    """عملکرد به تفکیک مبحث."""
    policy = get_scoring_policy(db)
    rows = db.execute(_base_query(db, student_id, from_date, to_date, subject_id)).all()
    topic_counts = _rows_to_topic_counts(db, rows)
    if not topic_counts:
        return []
    topics = db.execute(
        select(Topic, Chapter, Subject).join(Chapter, Topic.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
        .where(Topic.id.in_([uuid.UUID(t) for t in topic_counts]))
    ).all()
    result = []
    for topic, chapter, subject in topics:
        counts = topic_counts.get(str(topic.id), {"correct": 0, "wrong": 0, "blank": 0})
        result.append({
            "topic_id": str(topic.id), "topic": topic.title,
            "chapter": chapter.title, "subject": subject.name,
            **aggregate_counts(counts["correct"], counts["wrong"], counts["blank"], policy),
        })
    return sorted(result, key=lambda r: (r["percent_konkur"] is None, r["percent_konkur"] or 0))


def by_subject(db: Session, student_id: uuid.UUID, from_date: date | None,
               to_date: date | None) -> list[dict]:
    """عملکرد به تفکیک درس (AT-23)."""
    policy = get_scoring_policy(db)
    rows = db.execute(_base_query(db, student_id, from_date, to_date, None)).all()
    topic_counts = _rows_to_topic_counts(db, rows)
    if not topic_counts:
        return []
    subject_rows = db.execute(
        select(Subject, Topic.id)
        .join(Chapter, Chapter.subject_id == Subject.id)
        .join(Topic, Topic.chapter_id == Chapter.id)
        .where(Topic.id.in_([uuid.UUID(t) for t in topic_counts]))
    ).all()
    merged: dict[str, dict] = {}
    for subject, _topic_id in subject_rows:
        merged.setdefault(str(subject.id), {"subject": subject.name, "correct": 0,
                                            "wrong": 0, "blank": 0})
        counts = topic_counts.get(str(_topic_id))
        if counts:
            merged[str(subject.id)]["correct"] += counts["correct"]
            merged[str(subject.id)]["wrong"] += counts["wrong"]
            merged[str(subject.id)]["blank"] += counts["blank"]
    return [
        {"subject_id": sid, **row,
         **aggregate_counts(row["correct"], row["wrong"], row["blank"], policy)}
        for sid, row in sorted(merged.items(), key=lambda kv: kv[1]["subject"])
    ]


def by_difficulty(db: Session, student_id: uuid.UUID, from_date: date | None,
                  to_date: date | None) -> list[dict]:
    """عملکرد بر اساس سطح سختی — سوال بدون سختی نادیده گرفته می‌شود (قانون ۸.۶)."""
    policy = get_scoring_policy(db)
    stmt = select(TestRecord.result, Question.difficulty, func.count()).where(
        TestRecord.student_id == student_id,
        Question.difficulty.is_not(None),
    ).join(Question, TestRecord.question_id == Question.id)
    if from_date:
        stmt = stmt.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(TestRecord.solved_at <= datetime.combine(to_date, datetime.max.time()))
    rows = db.execute(stmt.group_by(TestRecord.result, Question.difficulty)).all()
    buckets: dict[str, dict[str, int]] = {
        "easy": {"correct": 0, "wrong": 0, "blank": 0},
        "medium": {"correct": 0, "wrong": 0, "blank": 0},
        "hard": {"correct": 0, "wrong": 0, "blank": 0},
    }
    for result, difficulty, cnt in rows:
        if difficulty in buckets and result in buckets[difficulty]:
            buckets[difficulty][result] += int(cnt)
    return [
        {"difficulty": difficulty, "label": {"easy": "آسان", "medium": "متوسط", "hard": "سخت"}[difficulty],
         **aggregate_counts(**counts, policy=policy)}
        for difficulty, counts in buckets.items()
    ]


def mistake_types(db: Session, student_id: uuid.UUID, from_date: date | None,
                  to_date: date | None) -> list[dict]:
    """آمار نوع اشتباهات (Mistake Pattern Analyzer)."""
    stmt = select(ErrorNote.error_type, func.count()).join(
        TestRecord, ErrorNote.test_record_id == TestRecord.id
    ).where(TestRecord.student_id == student_id)
    if from_date:
        stmt = stmt.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        stmt = stmt.where(TestRecord.solved_at <= datetime.combine(to_date, datetime.max.time()))
    rows = db.execute(stmt.group_by(ErrorNote.error_type)).all()
    labels = {"unknown": "بلد نبودن", "forgotten": "فراموشی", "careless": "بی‌دقتی", "time": "کمبود زمان"}
    total = sum(int(cnt) for _, cnt in rows)
    return [
        {"error_type": error_type, "label": labels.get(error_type, error_type),
         "count": int(cnt), "share": round(int(cnt) / total * 100, 1) if total else 0}
        for error_type, cnt in sorted(rows, key=lambda r: -int(r[1]))
    ]


def overview(db: Session, student_id: uuid.UUID, from_date: date | None,
             to_date: date | None) -> dict:
    """نمای کلی عملکرد در بازه — برای Today Hub و داشبورد."""
    from app.modules.activity.models import LearningActivity, ReviewItem

    policy = get_scoring_policy(db)
    test_q = select(TestRecord.result, func.count()).where(TestRecord.student_id == student_id)
    act_q = select(LearningActivity.type, func.sum(LearningActivity.duration_minutes)).where(
        LearningActivity.student_id == student_id
    )
    review_q = select(ReviewItem.status, func.count()).where(ReviewItem.student_id == student_id)
    if from_date:
        test_q = test_q.where(TestRecord.solved_at >= datetime.combine(from_date, datetime.min.time()))
        act_q = act_q.where(LearningActivity.started_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        test_q = test_q.where(TestRecord.solved_at <= datetime.combine(to_date, datetime.max.time()))
        act_q = act_q.where(LearningActivity.started_at <= datetime.combine(to_date, datetime.max.time()))

    result_counts = {"correct": 0, "wrong": 0, "blank": 0}
    for result, cnt in db.execute(test_q.group_by(TestRecord.result)).all():
        if result in result_counts:
            result_counts[result] = int(cnt)

    minutes_by_type = {t: int(m or 0) for t, m in db.execute(
        act_q.group_by(LearningActivity.type)).all()}
    review_counts = {s: int(c or 0) for s, c in db.execute(
        review_q.group_by(ReviewItem.status)).all()}

    return {
        "tests": {**result_counts, "total": sum(result_counts.values()),
                  **aggregate_counts(result_counts["correct"], result_counts["wrong"],
                                     result_counts["blank"], policy)},
        "study_minutes_by_type": minutes_by_type,
        "total_study_minutes": sum(v for k, v in minutes_by_type.items()
                                   if k in ("study", "review")),
        "review": {"pending": review_counts.get("pending", 0), "done": review_counts.get("done", 0)},
        "range": {"from": from_date.isoformat() if from_date else None,
                  "to": to_date.isoformat() if to_date else None},
    }
