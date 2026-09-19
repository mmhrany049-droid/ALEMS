"""سرویس آزمون — ایجاد، شروع، ثبت پاسخ‌ها، نمره‌دهی و نتیجه."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.events import event_bus
from app.modules.academic.models import Chapter, Question, Subject, Topic
from app.modules.academic.service import get_questions_bulk
from app.modules.activity.models import ErrorNote, TestRecord
from app.modules.exam.domain import ScoringPolicy, score_answers
from app.modules.exam.models import Exam, ExamAnswer, ExamQuestion, ExamResult
from app.modules.settings.service import get_exam_policy, get_scoring_policy
from app.shared.exceptions import ConflictError, NotFoundError, ValidationError


def create_exam(db: Session, student_id: uuid.UUID, data: dict) -> Exam:
    """ایجاد آزمون با سوالات انتخاب‌شده (AT-19)."""
    policy = get_exam_policy(db)
    question_ids = list(dict.fromkeys(data.pop("question_ids")))
    if len(question_ids) > policy.max_questions:
        raise ValidationError(
            f"حداکثر تعداد سوال در یک آزمون {policy.max_questions} است (قابل تنظیم در تنظیمات)."
        )
    get_questions_bulk(db, question_ids)

    exam = Exam(
        student_id=student_id,
        title=data["title"],
        exam_type=data["exam_type"],
        scheduled_at=data.get("scheduled_at") or datetime.utcnow(),
        duration_minutes=data.get("duration_minutes") or 60,
        status="planned",
    )
    db.add(exam)
    db.flush()
    for order, qid in enumerate(question_ids):
        db.add(ExamQuestion(exam_id=exam.id, question_id=qid, order_index=order))
    db.commit()
    db.refresh(exam)
    return exam


def list_exams(db: Session, student_id: uuid.UUID, limit: int = 50, offset: int = 0,
               status: str | None = None) -> tuple[list[Exam], int]:
    stmt = select(Exam).where(Exam.student_id == student_id)
    count_stmt = select(func.count()).select_from(Exam).where(Exam.student_id == student_id)
    if status:
        stmt = stmt.where(Exam.status == status)
        count_stmt = count_stmt.where(Exam.status == status)
    total = db.scalar(count_stmt) or 0
    rows = list(db.scalars(
        stmt.options(selectinload(Exam.result))
        .order_by(Exam.scheduled_at.desc()).offset(offset).limit(limit)
    ))
    return rows, int(total)


def get_exam(db: Session, student_id: uuid.UUID, exam_id: uuid.UUID) -> Exam:
    exam = db.get(Exam, exam_id)
    if exam is None or exam.student_id != student_id:
        raise NotFoundError("آزمون مورد نظر یافت نشد.")
    return exam


def start_exam(db: Session, student_id: uuid.UUID, exam_id: uuid.UUID) -> Exam:
    """شروع آزمون — تایمر و شرایط آزمون."""
    exam = get_exam(db, student_id, exam_id)
    if exam.status == "finished":
        raise ConflictError("این آزمون تمام شده و قابل شروع مجدد نیست.")
    if exam.status == "in_progress":
        return exam
    exam.status = "in_progress"
    exam.started_at = datetime.utcnow()
    db.commit()
    db.refresh(exam)
    return exam


def submit_exam(db: Session, student_id: uuid.UUID, exam_id: uuid.UUID,
                answers: list[dict]) -> ExamResult:
    """ثبت پاسخ‌ها و نمره‌دهی (AT-20/AT-21/AT-22).

    پاسخ هر سوال ذخیره، درصد کنکوری و بدون غلط محاسبه و تحلیل سختی تولید می‌شود.
    غلط‌های آزمون به‌صورت رکورد تست ثبت می‌شوند تا وارد چرخه مرور شوند.
    """
    exam = get_exam(db, student_id, exam_id)
    if exam.status == "finished":
        raise ConflictError("این آزمون قبلاً ثبت نهایی شده است.")
    if exam.status == "planned":
        exam.status = "in_progress"
        exam.started_at = exam.started_at or datetime.utcnow()

    exam_questions = list(db.scalars(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
    ))
    allowed_ids = {eq.question_id for eq in exam_questions}
    answer_map = {a["question_id"]: a for a in answers}
    unknown = set(answer_map) - allowed_ids
    if unknown:
        raise ValidationError(f"{len(unknown)} سوال ارسالی متعلق به این آزمون نیستند.")

    # سوالات پاسخ‌داده‌نشده = نزده
    for qid in allowed_ids - set(answer_map):
        answer_map[qid] = {"question_id": qid, "result": "blank", "duration_seconds": None}

    question_rows = {q.id: q for q in get_questions_bulk(db, list(allowed_ids))}
    scoring_answers = []
    for qid, answer in answer_map.items():
        result_value = answer["result"]
        if result_value not in ("correct", "wrong", "blank"):
            raise ValidationError("نتیجه هر پاسخ باید یکی از مقادیر correct/wrong/blank باشد.")
        scoring_answers.append({"question_id": str(qid), "result": result_value})

    policy = get_scoring_policy(db)
    difficulties = {str(q.id): q.difficulty for q in question_rows.values()}
    score = score_answers(scoring_answers, difficulties, policy)

    # ذخیره پاسخ‌ها
    db.query(ExamAnswer).filter(ExamAnswer.exam_id == exam.id).delete()
    for qid, answer in answer_map.items():
        db.add(ExamAnswer(
            exam_id=exam.id,
            question_id=qid,
            result=answer["result"],
            duration_seconds=answer.get("duration_seconds"),
        ))

    result = ExamResult(
        exam_id=exam.id,
        correct_count=score.correct,
        wrong_count=score.wrong,
        blank_count=score.blank,
        percent_konkur=score.percent_konkur,
        percent_no_penalty=score.percent_no_penalty,
        difficulty_breakdown=score.difficulty_breakdown,
        finished_at=datetime.utcnow(),
    )
    db.add(result)

    # ثبت رکوردهای تست برای ورود غلط‌ها به چرخه مرور و تحلیل‌ها
    for qid, answer in answer_map.items():
        db.add(TestRecord(
            student_id=student_id,
            question_id=qid,
            result=answer["result"],
            solved_at=result.finished_at,
            duration_seconds=answer.get("duration_seconds"),
        ))

    exam.status = "finished"
    db.commit()
    db.refresh(result)
    # رکوردهای تست آزمون به چرخه مرور اعلام می‌شوند (غلط‌های آزمون وارد صف مرور شوند)
    event_bus.emit("test_records.created", {
        "student_id": str(student_id), "count": len(answer_map), "source": "exam",
    })
    event_bus.emit("exam.finished", {"student_id": str(student_id), "exam_id": str(exam.id)})
    return result


def get_exam_result(db: Session, student_id: uuid.UUID, exam_id: uuid.UUID) -> dict:
    """نتیجه آزمون + تفکیک بر اساس درس."""
    exam = get_exam(db, student_id, exam_id)
    result = db.scalar(select(ExamResult).where(ExamResult.exam_id == exam.id))
    if result is None:
        raise NotFoundError("این آزمون هنوز ثبت نهایی نشده است؛ ابتدا پاسخ‌ها را ارسال کنید.")

    answers = list(db.scalars(select(ExamAnswer).where(ExamAnswer.exam_id == exam.id)))
    by_subject: dict[str, dict] = {}
    for answer in answers:
        question = db.get(Question, answer.question_id)
        subject_name = "نامشخص"
        if question:
            topic = db.get(Topic, question.topic_id)
            chapter = db.get(Chapter, topic.chapter_id) if topic else None
            subject = db.get(Subject, chapter.subject_id) if chapter else None
            if subject:
                subject_name = subject.name
        bucket = by_subject.setdefault(subject_name, {
            "subject": subject_name, "total": 0, "correct": 0, "wrong": 0, "blank": 0,
            "percent_konkur": None, "percent_no_penalty": None,
        })
        bucket["total"] += 1
        bucket[{"correct": "correct", "wrong": "wrong", "blank": "blank"}.get(answer.result, "blank")] += 1

    for bucket in by_subject.values():
        total = bucket["total"]
        bucket["percent_konkur"] = (
            round((bucket["correct"] - policy_penalty(db) * bucket["wrong"]) / total * 100, 2)
            if total else None
        )
        bucket["percent_no_penalty"] = round(bucket["correct"] / total * 100, 2) if total else None

    return {
        "exam": {
            "id": str(exam.id), "title": exam.title, "exam_type": exam.exam_type,
            "status": exam.status, "scheduled_at": exam.scheduled_at.isoformat(),
            "duration_minutes": exam.duration_minutes,
        },
        "result": {
            "correct_count": result.correct_count,
            "wrong_count": result.wrong_count,
            "blank_count": result.blank_count,
            "percent_konkur": round(result.percent_konkur, 2) if result.percent_konkur is not None else None,
            "percent_no_penalty": round(result.percent_no_penalty, 2) if result.percent_no_penalty is not None else None,
            "difficulty_breakdown": result.difficulty_breakdown,
            "finished_at": result.finished_at.isoformat(),
        },
        "by_subject": list(by_subject.values()),
    }


def policy_penalty(db: Session) -> float:
    policy = get_scoring_policy(db)
    return policy.wrong_penalty


def exam_payload(exam: Exam, question_count: int | None = None) -> dict:
    data = {
        "id": str(exam.id),
        "title": exam.title,
        "exam_type": exam.exam_type,
        "scheduled_at": exam.scheduled_at.isoformat(),
        "duration_minutes": exam.duration_minutes,
        "status": exam.status,
        "started_at": exam.started_at.isoformat() if exam.started_at else None,
    }
    if question_count is not None:
        data["question_count"] = question_count
    if exam.result is not None:
        data["percent_konkur"] = (
            round(exam.result.percent_konkur, 2) if exam.result.percent_konkur is not None else None
        )
        data["percent_no_penalty"] = (
            round(exam.result.percent_no_penalty, 2) if exam.result.percent_no_penalty is not None else None
        )
    return data
