"""Analytics — overview با سه بلوک جدا + برش‌ها (doc 12 §12.1، V2-A01).

ابعاد برش: subject(کتاب) · chapter · topic · difficulty · error_type · time_bucket.
داده‌ها از attempt_results/test_sessions/topics/questions/learning_states/error_notes
و حجم مطالعه از plan_tasks — همه با تاریخ تهران.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.academic.models import Question, Resource, Topic
from app.modules.activity.models import AttemptResult, ErrorNote, TestSession
from app.modules.analytics import domain
from app.modules.planning.models import PlanTask
from app.modules.review.models import LearningState, ReviewItem
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Student
from app.core.jalali import gregorian_to_jalali

logger = logging.getLogger("alems.analytics")

TZ_TEHRAN = dt.timezone(dt.timedelta(hours=3, minutes=30))


def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).astimezone(TZ_TEHRAN).date()


def _jalali_str(d: dt.date) -> str:
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def _aw(x: dt.datetime | None) -> dt.datetime | None:
    """naive (SQLite UTC) → aware — برای مقایسه با کرانه‌های پنجره."""
    if x is None:
        return None
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone.utc)


def _tehran_date(x: dt.datetime) -> dt.date:
    if x.tzinfo is None:
        x = x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(TZ_TEHRAN).date()


def _tehran_hour(x: dt.datetime) -> int:
    if x.tzinfo is None:
        x = x.replace(tzinfo=dt.timezone.utc)
    return x.astimezone(TZ_TEHRAN).hour


# --- بارگذاری داده‌های خام -------------------------------------------------------------

def _load(db: Session, student: Student) -> dict[str, Any]:
    """یک پاس خام — aggregation در Python (مقیاس SQLite یک دانش‌آموز)."""
    resources = db.execute(select(Resource).where(Resource.student_id == student.id)).scalars().all()
    res_ids = [r.id for r in resources]
    topics = (
        db.execute(select(Topic).where(Topic.resource_id.in_(res_ids))).scalars().all() if res_ids else []
    )
    topic_ids = [t.id for t in topics]
    questions = (
        db.execute(select(Question).where(Question.topic_id.in_(topic_ids))).scalars().all()
        if topic_ids
        else []
    )
    attempts = db.execute(
        select(AttemptResult).where(AttemptResult.student_id == student.id)
    ).scalars().all()
    sessions = db.execute(
        select(TestSession).where(TestSession.student_id == student.id)
    ).scalars().all()
    states = db.execute(
        select(LearningState).where(LearningState.student_id == student.id)
    ).scalars().all()
    notes = db.execute(select(ErrorNote).where(ErrorNote.student_id == student.id)).scalars().all()
    review_items = db.execute(
        select(ReviewItem).where(ReviewItem.student_id == student.id)
    ).scalars().all()
    plan_tasks = db.execute(
        select(PlanTask).where(PlanTask.student_id == student.id)
    ).scalars().all()

    topic_by_id = {t.id: t for t in topics}
    topic_resource = {t.id: t.resource_id for t in topics}
    question_topic = {q.id: q.topic_id for q in questions}
    question_diff = {q.id: q.difficulty for q in questions}
    # فصل = والد ساختاری موضوع
    chapter_of_topic = {
        t.id: (topic_by_id[t.parent_id].title if t.parent_id and t.parent_id in topic_by_id else None)
        for t in topics
    }

    return {
        "student": student,
        "resources": resources,
        "topics": topics,
        "questions": questions,
        "attempts": attempts,
        "sessions": sessions,
        "states": states,
        "notes": notes,
        "review_items": review_items,
        "plan_tasks": plan_tasks,
        "topic_by_id": topic_by_id,
        "topic_resource": topic_resource,
        "question_topic": question_topic,
        "question_diff": question_diff,
        "chapter_of_topic": chapter_of_topic,
    }


def _attempt_topic(a: AttemptResult, raw: dict) -> str | None:
    if a.topic_id:
        return a.topic_id
    if a.question_id and a.question_id in raw["question_topic"]:
        return raw["question_topic"][a.question_id]
    return None


def _acc(correct: int, wrong: int) -> dict[str, Any]:
    return {"correct": correct, "wrong": wrong, "answered_accuracy": domain.answered_accuracy(correct, wrong)}


# --- coverage تجمعی (کل دوران — پنجره ندارد) ------------------------------------------------

def coverage_cumulative(db: Session, student: Student, raw: dict[str, Any] | None = None) -> dict[str, Any]:
    raw = raw or _load(db, student)
    non_structural = [t for t in raw["topics"] if not t.is_structural]
    attempted_topics = {_attempt_topic(a, raw) for a in raw["attempts"]}
    attempted_topics.discard(None)
    attempted_questions = {a.question_id for a in raw["attempts"] if a.question_id}
    by_resource = []
    for r in raw["resources"]:
        r_topics = [t for t in non_structural if t.resource_id == r.id]
        r_attempted = [t for t in r_topics if t.id in attempted_topics]
        by_resource.append(
            {
                "resource_id": r.id,
                "title": r.title,
                "subject": r.subject,
                "topics_total": len(r_topics),
                "topics_attempted": len(r_attempted),
                "topics_ratio": domain.ratio(len(r_attempted), len(r_topics)),
            }
        )
    return domain.coverage_block(
        topics_total=len(non_structural),
        topics_attempted=len([t for t in non_structural if t.id in attempted_topics]),
        questions_total=len(raw["questions"]),
        questions_attempted=len(attempted_questions),
        by_resource=by_resource,
    )


# --- overview (V2-A01) ------------------------------------------------------------------

def overview(db: Session, student: Student, days: int = 30) -> dict[str, Any]:
    days = max(1, min(days, 365))
    raw = _load(db, student)
    settings = get_settings_map(db)
    k = float(settings.get("konkurs_penalty_k", 0.33))

    end = _today()
    start = end - dt.timedelta(days=days - 1)
    start_utc = dt.datetime.combine(start, dt.time.min, tzinfo=TZ_TEHRAN).astimezone(dt.timezone.utc)

    coverage = coverage_cumulative(db, student, raw)

    # --- دقت و حجم در پنجره
    win_attempts = [a for a in raw["attempts"] if _aw(a.solved_at) and _aw(a.solved_at) >= start_utc]
    win_sessions = [s for s in raw["sessions"] if _aw(s.started_at) and _aw(s.started_at) >= start_utc]

    # §8.1 — T از جلسات می‌آید (کل سوالات)، نه از ردیف‌های تلاش؛
    # بی‌پاسخ ≠ واردنشده ≠ خالی (قید ۳) — ستون‌های جلسه منبع حقیقت‌اند.
    correct = sum(s.correct_count or 0 for s in win_sessions)
    wrong = sum(s.wrong_count or 0 for s in win_sessions)
    unanswered = sum(s.unanswered_count or 0 for s in win_sessions)
    not_entered = sum(s.not_entered_count or 0 for s in win_sessions)
    total = sum(s.total_count or 0 for s in win_sessions)
    percent_konkur = round((correct - k * wrong) / total * 100, 2) if total else None
    percent_no_penalty = round(correct / total * 100, 2) if total else None
    accuracy = domain.accuracy_block(correct, wrong, unanswered, not_entered, percent_konkur, percent_no_penalty, k)
    done_tasks = [t for t in raw["plan_tasks"] if t.status == "done" and t.date and start <= t.date <= end]
    study_minutes = sum(t.minutes for t in done_tasks)
    active = {_tehran_date(a.solved_at) for a in win_attempts if a.solved_at}
    active |= {t.date for t in done_tasks}
    reviews_done = sum(
        1 for r in raw["review_items"] if _aw(r.last_reviewed_at) and _aw(r.last_reviewed_at) >= start_utc
    )
    duration_seconds = sum(a.duration_seconds or 0 for a in win_attempts)
    volume = domain.volume_block(
        attempts=len(win_attempts), sessions=len(win_sessions), study_minutes=study_minutes,
        active_days=len(active), reviews_done=reviews_done, duration_seconds=duration_seconds,
    )

    # --- time_bucket (دقت در هر بازه ساعت — جدا)
    buckets: dict[str, dict[str, int]] = {}
    for a in win_attempts:
        if not a.solved_at:
            continue
        b = buckets.setdefault(domain.time_bucket_fa(_tehran_hour(a.solved_at)), {"attempts": 0, "correct": 0, "wrong": 0})
        b["attempts"] += 1
        if a.result == "correct":
            b["correct"] += 1
        elif a.result == "wrong":
            b["wrong"] += 1
    time_buckets = [
        {"bucket": name, **b, "answered_accuracy": domain.answered_accuracy(b["correct"], b["wrong"])}
        for name, b in sorted(buckets.items(), key=lambda x: TIME_ORDER.index(x[0]) if x[0] in TIME_ORDER else 9)
    ]

    # --- سری روزانه برای نمودار (Recharts)
    daily_by_date: dict[dt.date, dict[str, Any]] = {}
    for i in range(days):
        d = start + dt.timedelta(days=i)
        daily_by_date[d] = {"date": d.isoformat(), "date_jalali": _jalali_str(d), "attempts": 0,
                            "correct": 0, "wrong": 0, "study_minutes": 0, "sessions": 0}
    for a in win_attempts:
        if not a.solved_at:
            continue
        row = daily_by_date.get(_tehran_date(a.solved_at))
        if row is None:
            continue
        row["attempts"] += 1
        if a.result == "correct":
            row["correct"] += 1
        elif a.result == "wrong":
            row["wrong"] += 1
    for t in done_tasks:
        row = daily_by_date.get(t.date)
        if row is not None:
            row["study_minutes"] += t.minutes
    for s in win_sessions:
        row = daily_by_date.get(_tehran_date(_aw(s.started_at)))
        if row is not None:
            row["sessions"] += 1
    daily = list(daily_by_date.values())

    # --- نقاط ضعف (از learning_states — پوشش/دقت/آمادگی جدا)
    weaknesses = [
        {
            "topic_id": st.topic_id,
            "topic_title": _topic_title(db, st.topic_id),
            "coverage": st.coverage,
            "accuracy": st.accuracy,
            "exam_readiness": st.exam_readiness,
            "confidence": st.confidence,
        }
        for st in sorted((s for s in raw["states"] if s.weakness), key=lambda s: s.exam_readiness)[:5]
    ]

    return {
        "window": {"days": days, "start": start.isoformat(), "end": end.isoformat(),
                   "start_jalali": _jalali_str(start), "end_jalali": _jalali_str(end)},
        "coverage": coverage,   # بلوک ۱ — V2-A01: جدا
        "accuracy": accuracy,   # بلوک ۲ — جدا
        "volume": volume,       # بلوک ۳ — جدا
        "time_buckets": time_buckets,
        "daily": daily,
        "weaknesses": weaknesses,
        "konkurs_target": domain.target_message_fa(
            student.target, accuracy["answered_accuracy"], coverage["topics_ratio"]
        ),
    }


TIME_ORDER = ["صبح", "ظهر", "عصر", "شب"]


def _topic_title(db: Session, topic_id: str | None) -> str | None:
    if not topic_id:
        return None
    return db.execute(select(Topic.title).where(Topic.id == topic_id)).scalar_one_or_none()


# --- برش‌ها (doc 12 §12.1) ------------------------------------------------------------------

def by_subject(db: Session, student: Student) -> dict[str, Any]:
    """برش subject/کتاب — سه متریک در هر ردیف جدا."""
    raw = _load(db, student)
    out = []
    for r in raw["resources"]:
        r_topics = [t for t in raw["topics"] if t.resource_id == r.id and not t.is_structural]
        r_topic_ids = {t.id for t in r_topics}
        r_questions = [q for q in raw["questions"] if q.topic_id in r_topic_ids]
        r_attempts = [a for a in raw["attempts"] if (_attempt_topic(a, raw) in r_topic_ids)]
        attempted_t = {_attempt_topic(a, raw) for a in r_attempts} & r_topic_ids
        attempted_q = {a.question_id for a in r_attempts if a.question_id}
        correct = sum(1 for a in r_attempts if a.result == "correct")
        wrong = sum(1 for a in r_attempts if a.result == "wrong")
        r_sessions = [s for s in raw["sessions"] if s.resource_id == r.id]
        out.append(
            {
                "resource_id": r.id,
                "title": r.title,
                "subject": r.subject,
                "coverage": {
                    "topics_total": len(r_topics),
                    "topics_attempted": len(attempted_t),
                    "topics_ratio": domain.ratio(len(attempted_t), len(r_topics)),
                    "questions_total": len(r_questions),
                    "questions_attempted": len(attempted_q),
                },
                "accuracy": _acc(correct, wrong),
                "volume": {
                    "attempts": len(r_attempts),
                    "sessions": len(r_sessions),
                    "duration_minutes": sum(a.duration_seconds or 0 for a in r_attempts) // 60,
                },
            }
        )
    out.sort(key=lambda x: -x["volume"]["attempts"])
    return {"items": out}


def by_chapter(db: Session, student: Student) -> dict[str, Any]:
    """برش chapter — فصل = والد ساختاری در tree (doc 09)."""
    raw = _load(db, student)
    chapters: dict[tuple[str | None, str], dict[str, Any]] = {}
    for t in raw["topics"]:
        if t.is_structural:
            continue
        res = next((r for r in raw["resources"] if r.id == t.resource_id), None)
        key = (raw["chapter_of_topic"].get(t.id), res.title if res else "?")
        c = chapters.setdefault(key, {"topics_total": 0, "topics_attempted": 0, "correct": 0, "wrong": 0, "attempts": 0})
        c["topics_total"] += 1
    attempted = {_attempt_topic(a, raw) for a in raw["attempts"]}
    for t in raw["topics"]:
        if t.is_structural:
            continue
        if t.id in attempted:
            res = next((r for r in raw["resources"] if r.id == t.resource_id), None)
            key = (raw["chapter_of_topic"].get(t.id), res.title if res else "?")
            chapters[key]["topics_attempted"] += 1
    for a in raw["attempts"]:
        tid = _attempt_topic(a, raw)
        t = raw["topic_by_id"].get(tid) if tid else None
        if t is None:
            continue
        res = next((r for r in raw["resources"] if r.id == t.resource_id), None)
        key = (raw["chapter_of_topic"].get(t.id), res.title if res else "?")
        c = chapters[key]
        c["attempts"] += 1
        if a.result == "correct":
            c["correct"] += 1
        elif a.result == "wrong":
            c["wrong"] += 1
    items = [
        {
            "chapter_title": k[0] or "(بدون فصل)",
            "book_title": k[1],
            "coverage": {"topics_total": v["topics_total"], "topics_attempted": v["topics_attempted"],
                         "topics_ratio": domain.ratio(v["topics_attempted"], v["topics_total"])},
            "accuracy": _acc(v["correct"], v["wrong"]),
            "volume": {"attempts": v["attempts"]},
        }
        for k, v in chapters.items()
    ]
    items.sort(key=lambda x: -x["volume"]["attempts"])
    return {"items": items}


def by_topic(
    db: Session, student: Student, order: str = "volume", limit: int = 20
) -> dict[str, Any]:
    """برش topic — پوشش/دقت/حجم هر موضوع جدا + exam_readiness از learning state."""
    raw = _load(db, student)
    limit = max(1, min(limit, 100))
    state_by_topic = {s.topic_id: s for s in raw["states"]}
    agg: dict[str, dict[str, Any]] = {}
    for t in raw["topics"]:
        if t.is_structural:
            continue
        res = next((r for r in raw["resources"] if r.id == t.resource_id), None)
        qs = [q for q in raw["questions"] if q.topic_id == t.id]
        agg[t.id] = {
            "topic_id": t.id,
            "topic_title": t.title,
            "book_title": res.title if res else None,
            "chapter_title": raw["chapter_of_topic"].get(t.id),
            "correct": 0, "wrong": 0, "attempts": 0, "duration_seconds": 0,
            "questions_total": len(qs), "questions_attempted": set(),
        }
    for a in raw["attempts"]:
        tid = _attempt_topic(a, raw)
        row = agg.get(tid)
        if row is None:
            continue
        row["attempts"] += 1
        row["duration_seconds"] += a.duration_seconds or 0
        if a.result == "correct":
            row["correct"] += 1
        elif a.result == "wrong":
            row["wrong"] += 1
        if a.question_id:
            row["questions_attempted"].add(a.question_id)

    items = []
    for tid, v in agg.items():
        st = state_by_topic.get(tid)
        qa = len(v["questions_attempted"])
        items.append(
            {
                "topic_id": tid,
                "topic_title": v["topic_title"],
                "book_title": v["book_title"],
                "chapter_title": v["chapter_title"],
                "coverage": {"questions_total": v["questions_total"], "questions_attempted": qa,
                             "questions_ratio": domain.ratio(qa, v["questions_total"])},
                "accuracy": _acc(v["correct"], v["wrong"]),
                "volume": {"attempts": v["attempts"], "duration_minutes": v["duration_seconds"] // 60},
                "exam_readiness": st.exam_readiness if st else None,
                "weakness": bool(st.weakness) if st else False,
            }
        )
    if order == "accuracy":
        items.sort(key=lambda x: (x["accuracy"]["answered_accuracy"] is None, x["accuracy"]["answered_accuracy"] or 0))
    elif order == "readiness":
        items.sort(key=lambda x: (x["exam_readiness"] is None, x["exam_readiness"] or 0))
    else:
        items.sort(key=lambda x: -x["volume"]["attempts"])
    return {"items": items[:limit], "order": order, "total": len(items)}


def by_difficulty(db: Session, student: Student) -> dict[str, Any]:
    """برش difficulty سوال — دقت در هر سطح جدا."""
    raw = _load(db, student)
    agg: dict[Any, dict[str, int]] = {}
    for a in raw["attempts"]:
        diff = raw["question_diff"].get(a.question_id) if a.question_id else None
        row = agg.setdefault(diff, {"attempts": 0, "correct": 0, "wrong": 0})
        row["attempts"] += 1
        if a.result == "correct":
            row["correct"] += 1
        elif a.result == "wrong":
            row["wrong"] += 1
    items = [
        {
            "difficulty": diff,
            "difficulty_fa": f"سطح {diff}" if diff is not None else "نامشخص",
            "volume": {"attempts": v["attempts"]},
            "accuracy": _acc(v["correct"], v["wrong"]),
        }
        for diff, v in sorted(agg.items(), key=lambda x: (x[0] is None, x[0] or 0))
    ]
    return {"items": items}


def mistakes(db: Session, student: Student) -> dict[str, Any]:
    """برش error_type + غلط‌های تکراری — انواع خطا هرگز با هم قاطی نمی‌شوند."""
    raw = _load(db, student)
    by_type: dict[str | None, int] = {}
    for n in raw["notes"]:
        by_type[n.error_type] = by_type.get(n.error_type, 0) + 1
    by_error_type = [
        {"error_type": t, "error_type_fa": domain.ERROR_TYPE_FA.get(t, t or "بدون برچسب"), "count": c}
        for t, c in sorted(by_type.items(), key=lambda x: -x[1])
    ]

    wrong_by_topic: dict[str, int] = {}
    for a in raw["attempts"]:
        if a.result != "wrong":
            continue
        tid = _attempt_topic(a, raw)
        title = raw["topic_by_id"][tid].title if tid in raw["topic_by_id"] else (a.topic_title or "نامشخص")
        wrong_by_topic[title] = wrong_by_topic.get(title, 0) + 1
    top_wrong_topics = [
        {"topic_title": t, "wrong_count": c}
        for t, c in sorted(wrong_by_topic.items(), key=lambda x: -x[1])[:8]
    ]

    repeated = [
        {
            "topic_title": r.topic_title,
            "book_title": r.book_title,
            "question_number": r.question_number,
            "wrong_count": r.wrong_count,
            "critical": r.critical,
        }
        for r in sorted((r for r in raw["review_items"] if r.wrong_count >= 2), key=lambda r: -r.wrong_count)[:10]
    ]

    unlabeled = sum(1 for n in raw["notes"] if not n.error_type)
    return {
        "by_error_type": by_error_type,
        "top_wrong_topics": top_wrong_topics,
        "repeated_wrong_questions": repeated,
        "notes_total": len(raw["notes"]),
        "notes_unlabeled": unlabeled,
    }


# --- میان‌برهای بازه (report و export از این‌ها استفاده می‌کنند) ---------------------------------

def range_facts(db: Session, student: Student, start: dt.date, end: dt.date) -> dict[str, Any]:
    """واقعیت‌های یک بازه تاریخ (تهران) — برای گزارش روزانه/هفتگی/ماهانه."""
    raw = _load(db, student)
    start_utc = dt.datetime.combine(start, dt.time.min, tzinfo=TZ_TEHRAN).astimezone(dt.timezone.utc)
    end_utc = dt.datetime.combine(end + dt.timedelta(days=1), dt.time.min, tzinfo=TZ_TEHRAN).astimezone(dt.timezone.utc)

    att = [a for a in raw["attempts"] if _aw(a.solved_at) and start_utc <= _aw(a.solved_at) < end_utc]
    sessions = [s for s in raw["sessions"] if _aw(s.started_at) and start_utc <= _aw(s.started_at) < end_utc]
    # شمارش‌ها از ستون‌های جلسه (§8.1) — بی‌پاسخ‌ها گم نمی‌شوند
    correct = sum(s.correct_count or 0 for s in sessions)
    wrong = sum(s.wrong_count or 0 for s in sessions)
    unanswered = sum(s.unanswered_count or 0 for s in sessions)
    not_entered = sum(s.not_entered_count or 0 for s in sessions)
    done_tasks = [t for t in raw["plan_tasks"] if t.status == "done" and t.date and start <= t.date <= end]
    all_tasks = [t for t in raw["plan_tasks"] if t.date and start <= t.date <= end]
    reviews = [r for r in raw["review_items"] if _aw(r.last_reviewed_at) and start_utc <= _aw(r.last_reviewed_at) < end_utc]
    active = {_tehran_date(a.solved_at) for a in att} | {t.date for t in done_tasks}

    per_topic: dict[str | None, int] = {}
    for a in att:
        tid = _attempt_topic(a, raw)
        if tid:
            per_topic[tid] = per_topic.get(tid, 0) + 1
    top_topics = [
        {"topic_id": tid, "topic_title": raw["topic_by_id"][tid].title if tid in raw["topic_by_id"] else None, "attempts": c}
        for tid, c in sorted(per_topic.items(), key=lambda x: -x[1])[:5]
    ]

    return {
        "attempts": len(att),
        "total_questions": sum(s.total_count or 0 for s in sessions),
        "correct": correct,
        "wrong": wrong,
        "unanswered": unanswered,
        "not_entered": not_entered,
        "sessions": len(sessions),
        "session_items": [
            {"id": s.id, "label": s.label, "resource_title": s.resource_title, "finished": s.finished_at is not None,
             "total_count": s.total_count, "correct_count": s.correct_count, "wrong_count": s.wrong_count,
             "percent_konkur": s.percent_konkur, "percent_no_penalty": s.percent_no_penalty}
            for s in sorted(sessions, key=lambda s: s.started_at)
        ],
        "study_minutes": sum(t.minutes for t in done_tasks),
        "test_duration_minutes": sum(a.duration_seconds or 0 for a in att) // 60,
        "tasks_done": len(done_tasks),
        "tasks_total": len(all_tasks),
        "reviews_done": len(reviews),
        "active_days": len(active),
        "top_topics": top_topics,
        "answered_accuracy": domain.answered_accuracy(correct, wrong),
    }
