"""Exam Center — سرویس (doc 12 §12.2، doc 08 §8.1، doc 06 §Exam).

چرخه عمر: planned → in_progress → finished (یا cancelled از planned/in_progress).
submit: جمع شمارش sessionهای تست (خودکار، با اتصال exam_id) یا شمارش دستی.
scoring snapshot همیشه درصد کنکوری و بدون‌جریمه را جدا نگه می‌دارد.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from fastapi.exceptions import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.events import EXAM_FINISHED, Event, event_bus
from app.core.jalali import gregorian_to_jalali
from app.modules.academic.models import Resource, Topic
from app.modules.activity.models import AttemptResult, TestSession
from app.modules.exam import domain
from app.modules.exam.models import Exam
from app.modules.planning.service import parse_date
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Student

logger = logging.getLogger("alems.exam")

MSG_EXAM_NOT_FOUND = "آزمون پیدا نشد."
MSG_SESSION_NOT_FOUND = "جلسه آزمون پیدا نشد."
MSG_BAD_TRANSITION = "این تغییر وضعیت با وضعیت فعلی آزمون سازگار نیست."
MSG_SUBMIT_EMPTY = "برای ثبت نتیجه، جلسه آزمون را انتخاب کن یا شمارش دستی بده."
MSG_COUNTS_INCOMPLETE = "شمارش دستی ناقص است — تعداد کل، درست و غلط لازم است."
MSG_TITLE_EMPTY = "عنوان آزمون نمی‌تواند خالی باشد."

_TZ = dt.timezone.utc


def _utcnow() -> dt.datetime:
    return dt.datetime.now(_TZ)


def _today() -> dt.date:
    return _utcnow().astimezone(dt.timezone(dt.timedelta(hours=3, minutes=30))).date()


def _iso(d: dt.date | dt.datetime | None) -> str | None:
    if d is None:
        return None
    return d.isoformat() if isinstance(d, dt.date) and not isinstance(d, dt.datetime) else d.date().isoformat()


def _jalali_str(d: dt.date | None) -> str | None:
    if d is None:
        return None
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def _get(db: Session, student: Student, exam_id: str) -> Exam:
    row = db.execute(
        select(Exam).where(Exam.id == exam_id, Exam.student_id == student.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=MSG_EXAM_NOT_FOUND)
    return row


def exam_out(db: Session, e: Exam) -> dict[str, Any]:
    resource_title = None
    if e.resource_id:
        r = db.execute(select(Resource.title).where(Resource.id == e.resource_id)).scalar_one_or_none()
        resource_title = r
    return {
        "id": e.id,
        "kind": e.kind,
        "kind_fa": domain.KIND_LABELS_FA.get(e.kind, e.kind),
        "status": e.status,
        "status_fa": domain.STATUS_LABELS_FA.get(e.status, e.status),
        "title": e.title,
        "note": e.note,
        "resource_id": e.resource_id,
        "resource_title": resource_title,
        "scheduled_date": _iso(e.scheduled_date),
        "scheduled_date_jalali": _jalali_str(e.scheduled_date),
        "planned_duration_minutes": e.planned_duration_minutes,
        "subjects": list(e.subjects or []),
        "planned_topic_ids": list(e.planned_topic_ids or []),
        "actual_topic_ids": list(e.actual_topic_ids or []),
        "session_ids": list(e.session_ids or []),
        "actual_duration_seconds": e.actual_duration_seconds,
        "duration_fa": domain.duration_fa(e.actual_duration_seconds, e.planned_duration_minutes),
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "finished_at": e.finished_at.isoformat() if e.finished_at else None,
        "scoring": e.scoring,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


# --- CRUD --------------------------------------------------------------------------------

def list_exams(db: Session, student: Student, status: str | None = None) -> dict[str, Any]:
    q = select(Exam).where(Exam.student_id == student.id)
    if status:
        q = q.where(Exam.status == status)
    rows = db.execute(q.order_by(Exam.scheduled_date.desc().nullslast(), Exam.created_at.desc())).scalars().all()
    upcoming = upcoming_exams(db, student)
    return {"items": [exam_out(db, e) for e in rows], "upcoming_count": len(upcoming)}


def create_exam(db: Session, student: Student, data) -> dict[str, Any]:
    title = (data.title or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail=MSG_TITLE_EMPTY)
    sched = parse_date(data.scheduled_date) if data.scheduled_date else None
    if data.resource_id:
        exists = db.execute(
            select(Resource.id).where(Resource.id == data.resource_id, Resource.student_id == student.id)
        ).scalar_one_or_none()
        if exists is None:
            raise HTTPException(status_code=404, detail="کتاب پیدا نشد.")
    e = Exam(
        student_id=student.id,
        kind=data.kind,
        title=title[:200],
        note=data.note,
        resource_id=data.resource_id,
        scheduled_date=sched,
        planned_duration_minutes=data.planned_duration_minutes,
        subjects=[str(s)[:80] for s in (data.subjects or [])],
        planned_topic_ids=list(data.planned_topic_ids or []),
        status="planned",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(e)
    db.flush()
    logger.info("exam created id=%s kind=%s title=%s", e.id, e.kind, e.title)
    return exam_out(db, e)


def update_exam(db: Session, student: Student, exam_id: str, data) -> dict[str, Any]:
    e = _get(db, student, exam_id)
    if data.status is not None and data.status != e.status:
        if data.status == "cancelled":
            if not domain.can_transition("cancel", e.status):
                raise HTTPException(status_code=422, detail=MSG_BAD_TRANSITION)
            e.status = "cancelled"
        elif data.status == "planned" and e.status == "cancelled":
            e.status = "planned"  # بازگردانی از لغو
        else:
            raise HTTPException(status_code=422, detail=MSG_BAD_TRANSITION)
    if e.status == "finished":
        raise HTTPException(status_code=422, detail="آزمون تمام‌شده قابل ویرایش نیست — نتیجه یک سند است.")
    if data.title is not None:
        t = data.title.strip()
        if not t:
            raise HTTPException(status_code=422, detail=MSG_TITLE_EMPTY)
        e.title = t[:200]
    if data.scheduled_date is not None:
        e.scheduled_date = parse_date(data.scheduled_date) if data.scheduled_date else None
    if data.planned_duration_minutes is not None:
        e.planned_duration_minutes = data.planned_duration_minutes
    if data.subjects is not None:
        e.subjects = [str(s)[:80] for s in data.subjects]
    if data.planned_topic_ids is not None:
        e.planned_topic_ids = list(data.planned_topic_ids)
    if data.resource_id is not None:
        e.resource_id = data.resource_id or None
    if data.note is not None:
        e.note = data.note
    e.updated_at = _utcnow()
    db.flush()
    return exam_out(db, e)


def delete_exam(db: Session, student: Student, exam_id: str) -> dict[str, Any]:
    e = _get(db, student, exam_id)
    # sessionهای متصل فقط exam_id را از دست می‌دهند — خود جلسه‌ها سند فعالیت‌اند
    for sid in list(e.session_ids or []):
        s = db.execute(select(TestSession).where(TestSession.id == sid)).scalar_one_or_none()
        if s is not None and s.exam_id == e.id:
            s.exam_id = None
    db.delete(e)
    db.flush()
    return {"deleted": True, "id": exam_id}


# --- چرخه عمر ------------------------------------------------------------------------------

def start_exam(db: Session, student: Student, exam_id: str) -> dict[str, Any]:
    e = _get(db, student, exam_id)
    if not domain.can_transition("start", e.status):
        raise HTTPException(status_code=422, detail=MSG_BAD_TRANSITION)
    e.status = "in_progress"
    e.started_at = _utcnow()
    e.updated_at = _utcnow()
    db.flush()
    return exam_out(db, e)


def submit_exam(db: Session, student: Student, exam_id: str, data) -> dict[str, Any]:
    e = _get(db, student, exam_id)
    if not domain.can_transition("submit", e.status):
        raise HTTPException(status_code=422, detail=MSG_BAD_TRANSITION)

    settings = get_settings_map(db)
    k = float(settings.get("konkurs_penalty_k", 0.33))

    rows: list[dict[str, Any]] = []
    sessions: list[TestSession] = []
    topic_ids: set[str] = set()

    if data.session_ids:
        for sid in data.session_ids:
            s = db.execute(
                select(TestSession).where(TestSession.id == sid, TestSession.student_id == student.id)
            ).scalar_one_or_none()
            if s is None:
                raise HTTPException(status_code=404, detail=MSG_SESSION_NOT_FOUND)
            if s.finished_at is None:
                raise HTTPException(status_code=422, detail="جلسه باید تمام‌شده باشد تا نتیجه‌اش ثبت شود.")
            if s.exam_id and s.exam_id != e.id:
                raise HTTPException(status_code=422, detail="این جلسه به آزمون دیگری متصل است.")
            sessions.append(s)
            rows.append(
                {
                    "total_count": s.total_count,
                    "correct_count": s.correct_count,
                    "wrong_count": s.wrong_count,
                    "unanswered_count": s.unanswered_count,
                    "not_entered_count": s.not_entered_count,
                    "actual_duration_seconds": s.actual_duration or 0,
                }
            )
        # موضوعات واقعی از attemptهای جلسه‌ها (doc 12 §12.2 — actual_topic_ids بعد از اجرا)
        att_topics = db.execute(
            select(AttemptResult.topic_id)
            .where(AttemptResult.session_id.in_([s.id for s in sessions]), AttemptResult.topic_id.is_not(None))
            .distinct()
        ).scalars().all()
        topic_ids.update(att_topics)
    elif data.total_count is not None:
        # شمارش دستی — امتحان مدرسه بدون جلسه دیجیتال
        correct = data.correct_count or 0
        wrong = data.wrong_count or 0
        not_entered = data.not_entered_count or 0
        unanswered = data.unanswered_count
        if unanswered is None:
            unanswered = max(data.total_count - correct - wrong - not_entered, 0)
        if correct + wrong + not_entered + unanswered > data.total_count:
            raise HTTPException(status_code=422, detail=MSG_COUNTS_INCOMPLETE)
        rows.append(
            {
                "total_count": data.total_count,
                "correct_count": correct,
                "wrong_count": wrong,
                "unanswered_count": unanswered,
                "not_entered_count": not_entered,
                "actual_duration_seconds": (data.actual_duration_minutes or 0) * 60,
            }
        )
    else:
        raise HTTPException(status_code=422, detail=MSG_SUBMIT_EMPTY)

    counts = domain.merge_counts(rows)
    e.scoring = domain.scoring_snapshot(counts, k)
    if sessions:
        e.actual_duration_seconds = counts["actual_duration_seconds"] or None
        e.session_ids = sorted({*(e.session_ids or []), *[s.id for s in sessions]})
        for s in sessions:
            s.exam_id = e.id
    elif data.actual_duration_minutes:
        e.actual_duration_seconds = data.actual_duration_minutes * 60
    if topic_ids:
        e.actual_topic_ids = sorted({*(e.actual_topic_ids or []), *topic_ids})
    e.status = "finished"
    e.finished_at = _utcnow()
    e.updated_at = _utcnow()
    db.flush()

    event_bus.publish(
        Event(EXAM_FINISHED, {"student_id": student.id, "exam_id": e.id, "scoring": e.scoring})
    )
    logger.info(
        "exam submitted id=%s sessions=%d total=%d pk=%s pnp=%s",
        e.id, len(sessions), counts["total_count"],
        e.scoring["percent_konkur"], e.scoring["percent_no_penalty"],
    )
    return exam_out(db, e)


def exam_result(db: Session, student: Student, exam_id: str) -> dict[str, Any]:
    e = _get(db, student, exam_id)
    base = exam_out(db, e)

    sessions_out = []
    if e.session_ids:
        srows = db.execute(select(TestSession).where(TestSession.id.in_(e.session_ids))).scalars().all()
        for s in srows:
            sessions_out.append(
                {
                    "id": s.id,
                    "label": s.label,
                    "resource_title": s.resource_title,
                    "total_count": s.total_count,
                    "correct_count": s.correct_count,
                    "wrong_count": s.wrong_count,
                    "unanswered_count": s.unanswered_count,
                    "not_entered_count": s.not_entered_count,
                    "percent_konkur": s.percent_konkur,
                    "percent_no_penalty": s.percent_no_penalty,
                    "actual_duration": s.actual_duration,
                }
            )

    topics_out = []
    if e.actual_topic_ids:
        trows = db.execute(select(Topic).where(Topic.id.in_(e.actual_topic_ids))).scalars().all()
        tmap = {t.id: t for t in trows}
        rmap = {}
        for t in trows:
            rmap[t.id] = db.execute(select(Resource.title).where(Resource.id == t.resource_id)).scalar_one_or_none()
        topics_out = [
            {"topic_id": tid, "topic_title": tmap[tid].title if tid in tmap else None,
             "book_title": rmap.get(tid)}
            for tid in e.actual_topic_ids
        ]

    planned_titles = []
    if e.planned_topic_ids:
        prows = db.execute(select(Topic).where(Topic.id.in_(e.planned_topic_ids))).scalars().all()
        planned_titles = [{"topic_id": t.id, "topic_title": t.title} for t in prows]

    base["result"] = {
        "scoring": e.scoring,
        "sessions": sessions_out,
        "actual_topics": topics_out,
        "planned_topics": planned_titles,
        "duration_fa": domain.duration_fa(e.actual_duration_seconds, e.planned_duration_minutes),
        "is_mock": e.kind == "mock",
    }
    return base


# --- یکپارچگی با Today/Planning (doc 07.6 بخش ۵ — آزمون نزدیک) ------------------------------

def upcoming_exams(db: Session, student: Student, days: int = 7) -> list[dict[str, Any]]:
    """آزمون‌های planned/in_progress در `days` روز آینده — برای Today Hub و planner."""
    today = _today()
    end = today + dt.timedelta(days=days)
    rows = db.execute(
        select(Exam)
        .where(
            Exam.student_id == student.id,
            Exam.status.in_(["planned", "in_progress"]),
            Exam.scheduled_date.is_not(None),
            Exam.scheduled_date >= today,
            Exam.scheduled_date <= end,
        )
        .order_by(Exam.scheduled_date)
    ).scalars().all()
    return [
        {
            "id": e.id,
            "title": e.title,
            "kind": e.kind,
            "kind_fa": domain.KIND_LABELS_FA.get(e.kind, e.kind),
            "status": e.status,
            "status_fa": domain.STATUS_LABELS_FA.get(e.status, e.status),
            "scheduled_date": _iso(e.scheduled_date),
            "scheduled_date_jalali": _jalali_str(e.scheduled_date),
            "days_until": (e.scheduled_date - today).days,
            "subjects": list(e.subjects or []),
        }
        for e in rows
    ]
