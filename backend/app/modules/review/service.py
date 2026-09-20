"""Review & Learning — application services (doc 06 §Review, doc 10).

- rebuild: صف از wrong/marks/blank-اختیاری (doc 10 §10.1) — upsert، بدون duplicate؛
  absorbed فقط با «غلط جدید» برمی‌گردد (doc 10 §10.2)
- complete → scheduled بعدی طبق چرخه ۱-۳-۷-۱۴ از settings (doc 10 §10.2)
- postpone → تاریخ جابه‌جا، status pending
- cluster-suggestion (doc 10 §10.3): critical/سررسیدگذشته اول، سقف روزانه،
  خوشه ≥ min_cluster ترجیحاً با هم
- learning_states per topic (doc 10 §10.4) — فرمول‌ها در review.domain
- مصرف‌کننده رویداد: test finish / past import → rebuild خودکار (doc 03 §3.4)
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

from fastapi.exceptions import HTTPException
from sqlalchemy import func, select

from app.core.events import TEST_RECORDS_CREATED, Event, event_bus
from app.core.jalali import JalaliDate, gregorian_to_jalali, today_jalali
from app.db.session import session_scope
from app.modules.academic.models import Question, Resource, Topic
from app.modules.activity.models import AttemptResult, QuestionMark
from app.modules.review import domain
from app.modules.review.models import LearningState, ReviewItem
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Student

MSG_ITEM_NOT_FOUND = "آیتم مرور پیدا نشد."

_utcnow = lambda: dt.datetime.now(dt.timezone.utc)  # noqa: E731
_iso = lambda d: d.isoformat() if d else None  # noqa: E731


def _today() -> dt.date:
    """روز تهران (doc 03 §3.5) — لنگر زمان‌بندی مرور."""
    return today_jalali().to_gregorian()


def _jalali_str(d: dt.date | None) -> str | None:
    if d is None:
        return None
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return JalaliDate(jy, jm, jd).format()


def _aware(d: dt.datetime | None) -> dt.datetime | None:
    if d is None:
        return None
    return d.replace(tzinfo=dt.timezone.utc) if d.tzinfo is None else d


# --- داده‌های کمکی -----------------------------------------------------------------

def _attempt_maps(db, student_id: str, question_ids: list[str] | None = None):
    """latest attempt per question + wrong_count per question (تاریخچه append-only)."""
    stmt = (
        select(AttemptResult)
        .where(AttemptResult.student_id == student_id)
        .order_by(AttemptResult.created_at, AttemptResult.id)
    )
    if question_ids is not None:
        stmt = stmt.where(AttemptResult.question_id.in_(question_ids or ["-"]))
    rows = db.execute(stmt).scalars().all()
    latest: dict[str, AttemptResult] = {}
    wrong_counts: dict[str, int] = defaultdict(int)
    for a in rows:
        if a.question_id is None:
            continue
        latest[a.question_id] = a
        if a.result == "wrong":
            wrong_counts[a.question_id] += 1
    return latest, dict(wrong_counts), rows


def _question_info(db, question_ids: list[str]) -> dict[str, dict]:
    if not question_ids:
        return {}
    rows = db.execute(
        select(Question, Topic, Resource)
        .join(Topic, Topic.id == Question.topic_id)
        .join(Resource, Resource.id == Topic.resource_id)
        .where(Question.id.in_(question_ids))
    ).all()
    return {
        q.id: {"number": q.number, "topic_id": t.id, "topic_title": t.title, "book_title": r.title}
        for q, t, r in rows
    }


def _marks_map(db, student_id: str, question_ids: list[str]) -> dict[str, QuestionMark]:
    if not question_ids:
        return {}
    rows = db.execute(
        select(QuestionMark).where(
            QuestionMark.student_id == student_id, QuestionMark.question_id.in_(question_ids)
        )
    ).scalars().all()
    return {m.question_id: m for m in rows}


def _item_out(
    item: ReviewItem,
    intervals: list[int],
    today: dt.date,
    attempt: AttemptResult | None = None,
    mark: QuestionMark | None = None,
) -> dict:
    sched = item.scheduled_date
    return {
        "id": item.id,
        "question_id": item.question_id,
        "number": item.question_number,
        "topic_id": item.topic_id,
        "topic_title": item.topic_title,
        "book_title": item.book_title,
        "source": item.source,
        "source_fa": domain.SOURCE_LABELS_FA.get(item.source, item.source),
        "status": item.status,
        "critical": item.critical,
        "wrong_count": item.wrong_count,
        "review_count": item.review_count,
        "cycle_index": item.cycle_index,
        "cycle_length": len(intervals),
        "next_interval_days": intervals[item.cycle_index] if item.cycle_index < len(intervals) else None,
        "scheduled_date": _iso(sched),
        "scheduled_date_jalali": _jalali_str(sched),
        "overdue_days": max(0, (today - sched).days) if sched else 0,
        "your_answer": attempt.answer if attempt else None,
        "correct_answer": attempt.correct_answer if attempt else None,
        "marks": {
            "review": bool(mark.review) if mark else False,
            "important": bool(mark.important) if mark else False,
            "hard": bool(mark.hard) if mark else False,
        },
    }


def _due_items(db, student_id: str, today: dt.date) -> list[ReviewItem]:
    return (
        db.execute(
            select(ReviewItem)
            .where(
                ReviewItem.student_id == student_id,
                ReviewItem.status != "absorbed",
                ReviewItem.scheduled_date <= today,
            )
            .order_by(
                ReviewItem.critical.desc(),
                ReviewItem.scheduled_date.asc(),
                ReviewItem.wrong_count.desc(),
                ReviewItem.created_at.asc(),
            )
        )
        .scalars()
        .all()
    )


def _load_item(db, student: Student, item_id: str) -> ReviewItem:
    item = db.execute(
        select(ReviewItem).where(ReviewItem.id == item_id, ReviewItem.student_id == student.id)
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=MSG_ITEM_NOT_FOUND)
    return item


# --- rebuild -------------------------------------------------------------------------

def rebuild(db, student: Student) -> dict:
    """ساخت/به‌روزرسانی صف از wrong/marks/blank — idempotent، بدون duplicate."""
    settings = get_settings_map(db)
    intervals = settings["review_intervals"]
    include_blank = settings["include_blank_in_review"]
    today = _today()
    now = _utcnow()

    latest, wrong_counts, _rows = _attempt_maps(db, student.id)

    targets: dict[str, tuple[str, int, AttemptResult | None]] = {}
    for qid, a in latest.items():
        wc = wrong_counts.get(qid, 0)
        if a.result == "wrong":
            targets[qid] = ("wrong", wc, a)
        elif include_blank and a.status == "unanswered":
            # doc 08 §8.4 — blank اختیاری از settings
            targets[qid] = ("blank", wc, a)

    marks = db.execute(select(QuestionMark).where(QuestionMark.student_id == student.id)).scalars().all()
    for m in marks:
        if m.review:
            src = "mark_review"
        elif m.hard:
            src = "mark_hard"
        elif m.important:
            src = "mark_important"
        else:
            continue
        prev = targets.get(m.question_id)
        if prev is None or domain.source_priority(src) < domain.source_priority(prev[0]):
            targets[m.question_id] = (
                src,
                prev[1] if prev else wrong_counts.get(m.question_id, 0),
                prev[2] if prev else latest.get(m.question_id),
            )

    info = _question_info(db, list(targets.keys()))
    existing = {
        r.question_id: r
        for r in db.execute(select(ReviewItem).where(ReviewItem.student_id == student.id)).scalars().all()
    }

    added = updated = reopened = 0
    for qid, (source, wc, att) in targets.items():
        meta = info.get(qid) or {}
        number = meta.get("number") if meta.get("number") is not None else (att.question_number if att else None)
        topic_id = meta.get("topic_id") or (att.topic_id if att else None)
        topic_title = meta.get("topic_title") or (att.topic_title if att else None)
        book_title = meta.get("book_title")
        critical = domain.critical_flag(wc)

        item = existing.get(qid)
        if item is None:
            db.add(
                ReviewItem(
                    student_id=student.id,
                    question_id=qid,
                    topic_id=topic_id,
                    question_number=number,
                    topic_title=topic_title,
                    book_title=book_title,
                    source=source,
                    status="pending",
                    critical=critical,
                    wrong_count=wc,
                    cycle_index=0,
                    review_count=0,
                    scheduled_date=today,
                )
            )
            added += 1
            continue

        changed = False
        if item.wrong_count != wc:
            item.wrong_count = wc
            changed = True
        if item.critical != critical:
            item.critical = critical
            changed = True
        if domain.source_priority(source) < domain.source_priority(item.source):
            item.source = source
            changed = True
        for fld, val in (("topic_id", topic_id), ("topic_title", topic_title), ("book_title", book_title), ("question_number", number)):
            if val is not None and getattr(item, fld) != val:
                setattr(item, fld, val)
                changed = True

        if item.status == "absorbed" and source == "wrong":
            # doc 10 §10.2 — absorbed برنمی‌گردد مگر غلط جدید
            ref = _aware(item.last_reviewed_at or item.updated_at)
            att_at = _aware(att.created_at) if att is not None else None
            if att_at is not None and ref is not None and att_at > ref:
                item.status = "pending"
                item.cycle_index = 0
                item.review_count = 0
                item.scheduled_date = today
                reopened += 1
                changed = True
        if changed:
            item.updated_at = now
            updated += 1

    db.flush()
    states_count = recompute_learning_states(db, student)
    active = db.execute(
        select(func.count()).select_from(ReviewItem).where(
            ReviewItem.student_id == student.id, ReviewItem.status != "absorbed"
        )
    ).scalar_one()
    return {
        "added": added,
        "updated": updated,
        "reopened": reopened,
        "active": int(active),
        "learning_states": states_count,
        "intervals": intervals,
    }


# --- queue / complete / postpone -------------------------------------------------------

def queue(db, student: Student) -> dict:
    settings = get_settings_map(db)
    intervals = settings["review_intervals"]
    today = _today()
    items = _due_items(db, student.id, today)

    qids = [it.question_id for it in items]
    latest, _wc, _rows = _attempt_maps(db, student.id, qids)
    marks = _marks_map(db, student.id, qids)

    upcoming = db.execute(
        select(func.count()).select_from(ReviewItem).where(
            ReviewItem.student_id == student.id,
            ReviewItem.status != "absorbed",
            ReviewItem.scheduled_date > today,
        )
    ).scalar_one()
    absorbed = db.execute(
        select(func.count()).select_from(ReviewItem).where(
            ReviewItem.student_id == student.id, ReviewItem.status == "absorbed"
        )
    ).scalar_one()

    return {
        "items": [_item_out(it, intervals, today, latest.get(it.question_id), marks.get(it.question_id)) for it in items],
        "due_count": len(items),
        "upcoming_count": int(upcoming),
        "absorbed_count": int(absorbed),
        "intervals": intervals,
        "today_jalali": today_jalali().format(),
    }


def complete(db, student: Student, item_id: str) -> dict:
    settings = get_settings_map(db)
    intervals = settings["review_intervals"]
    today = _today()
    item = _load_item(db, student, item_id)

    nxt = domain.next_after_complete(item.cycle_index, intervals, today)
    item.status = nxt["status"]
    item.cycle_index = nxt["cycle_index"]
    item.scheduled_date = nxt["scheduled_date"]
    item.review_count += 1
    item.last_reviewed_at = _utcnow()
    item.updated_at = item.last_reviewed_at
    db.flush()

    # رویداد REVIEW_COMPLETED در router و «بعد از commit» publish می‌شود (الگوی خانه —
    # مصرف‌کننده rewards با session جدا می‌نویسد؛ قفل نوشتن SQLite باید آزاد باشد).
    latest, _wc, _rows = _attempt_maps(db, student.id, [item.question_id])
    marks = _marks_map(db, student.id, [item.question_id])
    return _item_out(item, intervals, today, latest.get(item.question_id), marks.get(item.question_id))


def postpone(db, student: Student, item_id: str, days: int = 1) -> dict:
    if not isinstance(days, int) or isinstance(days, bool) or not (1 <= days <= 30):
        raise HTTPException(status_code=422, detail="تأخیر باید بین ۱ تا ۳۰ روز باشد.")
    settings = get_settings_map(db)
    intervals = settings["review_intervals"]
    today = _today()
    item = _load_item(db, student, item_id)

    item.scheduled_date = domain.postpone_date(item.scheduled_date, today, days)
    item.status = "pending"  # doc 10 §10.1
    item.updated_at = _utcnow()
    db.flush()
    latest, _wc, _rows = _attempt_maps(db, student.id, [item.question_id])
    marks = _marks_map(db, student.id, [item.question_id])
    return _item_out(item, intervals, today, latest.get(item.question_id), marks.get(item.question_id))


# --- cluster (doc 10 §10.3) ----------------------------------------------------------------

def cluster_suggestion(db, student: Student) -> dict:
    settings = get_settings_map(db)
    intervals = settings["review_intervals"]
    budget = settings["max_daily_review"]
    min_cluster = settings["min_cluster"]
    today = _today()
    items = _due_items(db, student.id, today)

    qids = [it.question_id for it in items]
    latest, _wc, _rows = _attempt_maps(db, student.id, qids)
    marks = _marks_map(db, student.id, qids)
    outs = [_item_out(it, intervals, today, latest.get(it.question_id), marks.get(it.question_id)) for it in items]
    for out, it in zip(outs, items):
        out["scheduled_date"] = it.scheduled_date  # تاریخ خام برای محاسبه overdue در domain

    picked = domain.pick_cluster_suggestion(outs, today, budget, min_cluster)
    picked_ids = {p["id"] for p in picked}

    clusters_map: dict[str, dict] = {}
    for it in outs:
        key = it["topic_id"] or f"q:{it['id']}"
        c = clusters_map.setdefault(
            key,
            {"topic_id": it["topic_id"], "topic_title": it["topic_title"], "book_title": it["book_title"], "size": 0, "critical_count": 0, "suggested_count": 0},
        )
        c["size"] += 1
        if it["critical"]:
            c["critical_count"] += 1
        if it["id"] in picked_ids:
            c["suggested_count"] += 1
    clusters = sorted(clusters_map.values(), key=lambda c: (-c["critical_count"], -c["size"]))

    return {
        "suggested": picked,
        "suggested_count": len(picked),
        "clusters": clusters,
        "due_count": len(outs),
        "budget": budget,
        "min_cluster": min_cluster,
    }


# --- learning states (doc 10 §10.4) --------------------------------------------------------

def recompute_learning_states(db, student: Student) -> int:
    settings = get_settings_map(db)
    intervals_len = len(settings["review_intervals"])
    now = _utcnow()

    latest, wrong_counts, all_attempts = _attempt_maps(db, student.id)

    # review progress per question
    progress_map: dict[str, float] = {}
    for it in db.execute(select(ReviewItem).where(ReviewItem.student_id == student.id)).scalars().all():
        progress_map[it.question_id] = domain.review_progress(it.cycle_index, intervals_len, it.status == "absorbed")

    topic_ids = {a.topic_id for a in all_attempts if a.topic_id}
    topic_ids |= set(
        db.execute(select(LearningState.topic_id).where(LearningState.student_id == student.id)).scalars().all()
    )
    topic_ids = {t for t in topic_ids if t}

    existing_rows = {
        r.topic_id: r
        for r in db.execute(select(LearningState).where(LearningState.student_id == student.id)).scalars().all()
    }

    for tid in sorted(topic_ids):
        total_q = int(
            db.execute(select(func.count()).select_from(Question).where(Question.topic_id == tid)).scalar_one()
        )
        t_attempts = [a for a in all_attempts if a.topic_id == tid]
        if not t_attempts and tid not in existing_rows:
            continue
        latest_by_q: dict[str, AttemptResult] = {}
        attempted_qids: set[str] = set()
        for a in t_attempts:  # مرتب → آخرین برنده است
            if a.question_id is None:
                continue
            latest_by_q[a.question_id] = a
            if a.status != "not_entered":
                attempted_qids.add(a.question_id)
        correct_attempts = sum(1 for a in t_attempts if a.result == "correct")
        wrong_attempts = sum(1 for a in t_attempts if a.result == "wrong")
        valid_attempts = correct_attempts + wrong_attempts
        repeated = sum(1 for qid in latest_by_q if wrong_counts.get(qid, 0) >= 2)
        last_at = max((_aware(a.created_at) for a in t_attempts if a.created_at), default=None)
        days_since = ((now - last_at).total_seconds() / 86400.0) if last_at else None

        per_q: list[tuple[str, float]] = []
        for qid, a in latest_by_q.items():
            if a.status == "not_entered":
                continue
            prog = progress_map.get(qid)
            if prog is None:
                prog = 1.0 if a.result == "correct" else 0.0
            per_q.append((a.result, prog))

        st = domain.learning_state(
            total_questions=total_q,
            attempted_questions=len(attempted_qids),
            correct_attempts=correct_attempts,
            wrong_attempts=wrong_attempts,
            repeated_wrong_questions=repeated,
            valid_attempts=valid_attempts,
            days_since_last=days_since,
            per_question_retention=per_q,
        )

        row = existing_rows.get(tid)
        if row is None:
            row = LearningState(student_id=student.id, topic_id=tid)
            db.add(row)
            existing_rows[tid] = row
        for k, v in st.items():
            setattr(row, k, v)
        row.total_questions = total_q
        row.attempted_questions = len(attempted_qids)
        row.correct_count = correct_attempts
        row.wrong_count = wrong_attempts
        row.updated_at = now
    db.flush()
    return len(topic_ids)


def learning_states(db, student: Student) -> list[dict]:
    rows = db.execute(
        select(LearningState, Topic.title, Resource.title)
        .outerjoin(Topic, Topic.id == LearningState.topic_id)
        .outerjoin(Resource, Resource.id == Topic.resource_id)
        .where(LearningState.student_id == student.id)
        .order_by(LearningState.weakness.desc(), LearningState.exam_readiness.asc())
    ).all()
    return [
        {
            "id": s.id,
            "topic_id": s.topic_id,
            "topic_title": t_title or "—",
            "book_title": b_title,
            "coverage": s.coverage,
            "accuracy": s.accuracy,
            "retention_est": s.retention_est,
            "recency_score": s.recency_score,
            "repeated_error_score": s.repeated_error_score,
            "exam_readiness": s.exam_readiness,
            "confidence": s.confidence,
            "weakness": s.weakness,
            "total_questions": s.total_questions,
            "attempted_questions": s.attempted_questions,
            "correct_count": s.correct_count,
            "wrong_count": s.wrong_count,
            "updated_at": _iso(s.updated_at),
        }
        for s, t_title, b_title in rows
    ]


# --- marks → queue (doc 10 §10.1) ---------------------------------------------------------

def sync_marks_into_queue(db, student: Student, question_id: str, mark: QuestionMark) -> ReviewItem | None:
    """تیک review/important/hard → ورود/بازگشت به صف (فراخوانی از activity.put_marks)."""
    if not (mark.review or mark.important or mark.hard):
        return None
    source = "mark_review" if mark.review else ("mark_hard" if mark.hard else "mark_important")
    today = _today()
    item = db.execute(
        select(ReviewItem).where(ReviewItem.student_id == student.id, ReviewItem.question_id == question_id)
    ).scalar_one_or_none()
    wc = int(
        db.execute(
            select(func.count()).select_from(AttemptResult).where(
                AttemptResult.student_id == student.id,
                AttemptResult.question_id == question_id,
                AttemptResult.result == "wrong",
            )
        ).scalar_one()
    )
    if item is None:
        meta = _question_info(db, [question_id]).get(question_id) or {}
        item = ReviewItem(
            student_id=student.id,
            question_id=question_id,
            topic_id=meta.get("topic_id"),
            question_number=meta.get("number"),
            topic_title=meta.get("topic_title"),
            book_title=meta.get("book_title"),
            source=source,
            status="pending",
            critical=domain.critical_flag(wc),
            wrong_count=wc,
            cycle_index=0,
            review_count=0,
            scheduled_date=today,
        )
        db.add(item)
    else:
        if item.status == "absorbed":
            # تیک صریح کاربر = یک بازگشت (rebuild بدون غلط جدید این کار را نمی‌کند)
            item.status = "pending"
            item.cycle_index = 0
            item.review_count = 0
            item.scheduled_date = today
        if domain.source_priority(source) < domain.source_priority(item.source):
            item.source = source
        if item.wrong_count != wc:
            item.wrong_count = wc
            item.critical = domain.critical_flag(wc)
    db.flush()
    return item


# --- مصرف‌کننده رویداد (doc 03 §3.4) ---------------------------------------------------------

_consumers_registered = False


def register_event_consumers() -> None:
    """test finish / past import → rebuild صف + learning states (بدون شکست producer)."""
    global _consumers_registered
    if _consumers_registered:
        return
    _consumers_registered = True

    def _on_test_records(event: Event) -> None:
        if not (event.payload.get("finished") or event.payload.get("past")):
            return
        student_id = event.payload.get("student_id")
        if not student_id:
            return
        with session_scope() as db:
            student = db.execute(select(Student).where(Student.id == student_id)).scalar_one_or_none()
            if student is not None:
                rebuild(db, student)

    event_bus.subscribe(TEST_RECORDS_CREATED, _on_test_records)
