"""Activity & Test Engine — application services (doc 06 §Tests, doc 09 §9.2-9.4).

جریان (doc 09 §9.2):
1. create session (mode timed/untimed) — انتخاب با range/parity/count/difficulty
2. add records — هر رکورد یک ردیف attempt append-only اضافه می‌کند (V2-T05)
3. finish — scoring (doc 08 §8.1) + events + snapshot؛ **ایدمپوتنت** (V2-T02)

past import (doc 09 §9.3): ردیف‌ها می‌توانند not_entered باشند؛ تکمیل بعدی
«همان attempt» را به answered تبدیل می‌کند (نه duplicate) و درصد را به‌روز می‌کند.

time tracking (doc 09 §9.4): duration per attempt + aggregate per topic.
"""
from __future__ import annotations

import datetime as dt

from fastapi.exceptions import HTTPException
from sqlalchemy import select

from app.core.events import QUESTION_MARKS_CHANGED, TEST_RECORDS_CREATED, Event, event_bus
from app.core.versioning import get_meta_value
from app.modules.academic.models import AnswerKey, Question, Resource, Topic
from app.modules.academic.service import children_map_for
from app.modules.activity import domain
from app.modules.activity.models import AttemptResult, ErrorNote, QuestionMark, TestSession
from app.modules.student.models import Student

MSG_SESSION_NOT_FOUND = "جلسه پیدا نشد."
MSG_BOOK_NOT_FOUND = "کتاب پیدا نشد."
MSG_TOPIC_NOT_FOUND = "موضوع پیدا نشد."
MSG_NOTE_NOT_FOUND = "یادداشت پیدا نشد."
MSG_FINISHED_LOCKED = "جلسه پایان یافته است؛ تاریخچه نتایج قفل است (append-only)."
MSG_TIMED_NEEDS_DURATION = "برای حالت زمان‌دار، مدت زمان برنامه‌ریزی‌شده (ثانیه) را وارد کن."
MSG_RECORD_NEEDS_TARGET = "هر رکورد باید question_id یا number داشته باشد."
MSG_QUESTION_NOT_IN_SESSION = "سوال با این شماره در انتخاب جلسه نیست."
MSG_TOPICS_NOT_IN_BOOK = "بعضی موضوعات انتخابی به این کتاب تعلق ندارند."
MSG_BAD_RANGE = "شماره شروع نمی‌تواند بزرگ‌تر از شماره پایان باشد."

META_KEY_PENALTY_K = "konkur_penalty_k"  # doc 08 §8.1 — k از Settings (پیش‌فرض 0.33)

_utcnow = lambda: dt.datetime.now(dt.timezone.utc)  # noqa: E731


def _iso(d: dt.datetime | None) -> str | None:
    """همه timestampها UTC ذخیره می‌شوند؛ SQLite آن‌ها را naive برمی‌گرداند →
    برای پاسخ یکدست API، tz UTC را برمی‌گردانیم."""
    if d is None:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.isoformat()


def get_penalty_k(db) -> float:
    raw = get_meta_value(db, META_KEY_PENALTY_K, str(domain.DEFAULT_PENALTY_K))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return domain.DEFAULT_PENALTY_K


# --- helpers -------------------------------------------------------------------

def _owned_resource(db, student: Student, resource_id: str) -> Resource:
    resource = db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.student_id == student.id)
    ).scalar_one_or_none()
    if resource is None:
        raise HTTPException(status_code=404, detail=MSG_BOOK_NOT_FOUND)
    return resource


def _load_session(db, student: Student, session_id: str) -> TestSession:
    session = db.execute(
        select(TestSession).where(TestSession.id == session_id, TestSession.student_id == student.id)
    ).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail=MSG_SESSION_NOT_FOUND)
    return session


def _latest_key(db, question_id: str) -> tuple[str | None, int | None]:
    row = db.execute(
        select(AnswerKey).where(AnswerKey.question_id == question_id).order_by(AnswerKey.version.desc()).limit(1)
    ).scalar_one_or_none()
    return (row.answer, row.version) if row else (None, None)


def _expand_topic_ids(db, topic_ids: list[str]) -> list[str]:
    """انتخاب فصل/parent = همه نوادگان هم شامل می‌شوند (درخت کتاب)."""
    if not topic_ids:
        return []
    cmap = children_map_for(db, topic_ids)
    out: set[str] = set()
    stack = list(topic_ids)
    while stack:
        tid = stack.pop()
        if tid in out:
            continue
        out.add(tid)
        stack.extend(cmap.get(tid, []))
    return sorted(out)


def _select_questions(db, resource_id, topic_ids, from_number, to_number, parity, count, difficulty):
    expanded = _expand_topic_ids(db, topic_ids)
    stmt = (
        select(Question, Topic)
        .join(Topic, Topic.id == Question.topic_id)
        .where(Topic.resource_id == resource_id)
        .order_by(Topic.sort_order, Question.number, Question.id)
    )
    if expanded:
        stmt = stmt.where(Question.topic_id.in_(expanded))
    if difficulty is not None:
        stmt = stmt.where(Question.difficulty == difficulty)
    rows = db.execute(stmt).all()
    scope_count = len(rows)  # X در پیام «فقط X سوال با این شرایط وجود دارد.»

    keep = set(domain.filter_numbers([q.number for q, _ in rows], from_number, to_number, parity))
    filtered = [(q, t) for q, t in rows if q.number in keep]
    if count is not None:
        filtered = filtered[:count]
    return filtered, scope_count


def _questions_by_ids(db, ids: list[str]) -> list[tuple[Question, Topic]]:
    if not ids:
        return []
    rows = db.execute(
        select(Question, Topic).join(Topic, Topic.id == Question.topic_id).where(Question.id.in_(ids))
    ).all()
    by_id = {q.id: (q, t) for q, t in rows}
    return [by_id[i] for i in ids if i in by_id]  # ترتیب انتخاب جلسه حفظ می‌شود


def _attempt_key(a: AttemptResult) -> str:
    return a.question_id or f"n:{a.question_number}:{a.topic_id}"


def _load_attempts(db, session_id: str) -> list[AttemptResult]:
    return (
        db.execute(
            select(AttemptResult)
            .where(AttemptResult.session_id == session_id)
            .order_by(AttemptResult.created_at, AttemptResult.id)
        )
        .scalars()
        .all()
    )


def _latest_by_question(attempts: list[AttemptResult]) -> dict[str, AttemptResult]:
    """append-only: تاریخچه کامل می‌ماند؛ scoring آخرین ردیف هر سوال را می‌بیند."""
    latest: dict[str, AttemptResult] = {}
    for a in attempts:
        latest[_attempt_key(a)] = a  # لیست مرتب است → آخرین، برنده است
    return latest


def _sum_durations(attempts) -> int | None:
    vals = [a.duration_seconds for a in attempts if a.duration_seconds is not None]
    return sum(vals) if vals else None


def _session_out(s: TestSession) -> dict:
    return {
        "id": s.id,
        "mode": s.mode,
        "label": s.label,
        "resource_id": s.resource_id,
        "resource_title": s.resource_title,
        "source": s.source,
        "filters": s.filters or {},
        "total_count": s.total_count,
        "planned_duration": s.planned_duration,
        "actual_duration": s.actual_duration,
        "penalty_k": s.penalty_k,
        "correct_count": s.correct_count,
        "wrong_count": s.wrong_count,
        "unanswered_count": s.unanswered_count,
        "not_entered_count": s.not_entered_count,
        "percent_konkur": s.percent_konkur,
        "percent_no_penalty": s.percent_no_penalty,
        "started_at": _iso(s.started_at),
        "finished_at": _iso(s.finished_at),
        "finished": s.finished_at is not None,
    }


def _attempt_out(a: AttemptResult) -> dict:
    return {
        "id": a.id,
        "question_id": a.question_id,
        "topic_id": a.topic_id,
        "question_number": a.question_number,
        "topic_title": a.topic_title,
        "status": a.status,
        "result": a.result,
        "answer": a.answer,
        "correct_answer": a.correct_answer,
        "answer_key_version": a.answer_key_version,
        "duration_seconds": a.duration_seconds,
        "solved_at": _iso(a.solved_at),
    }


def _questions_for_session(db, session: TestSession, latest: dict[str, AttemptResult]) -> list[dict]:
    """لیست سوال‌های جلسه + آخرین وضعیت (correct_answer فقط بعد از finish)."""
    out = []
    seen: set[str] = set()
    for q, t in _questions_by_ids(db, session.selected_question_ids or []):
        a = latest.get(q.id)
        out.append(
            {
                "question_id": q.id,
                "number": q.number,
                "topic_id": t.id,
                "topic_title": t.title,
                "block_type": t.block_type,
                "difficulty": q.difficulty,
                "status": a.status if a else None,
                "result": a.result if a else None,
                "answer": a.answer if a else None,
                "correct_answer": a.correct_answer if (a and session.finished_at) else None,
                "duration_seconds": a.duration_seconds if a else None,
            }
        )
        seen.add(q.id)
    # past sessions / attemptهایی که سوالشان از انتخاب جلسه خارج است (history)
    for a in latest.values():
        if a.question_id and a.question_id in seen:
            continue
        out.append(
            {
                "question_id": a.question_id,
                "number": a.question_number,
                "topic_id": a.topic_id,
                "topic_title": a.topic_title,
                "block_type": None,
                "difficulty": None,
                "status": a.status,
                "result": a.result,
                "answer": a.answer,
                "correct_answer": a.correct_answer,
                "duration_seconds": a.duration_seconds,
            }
        )
    return out


def _topic_aggregate(session: TestSession, attempts: list[AttemptResult], latest: dict[str, AttemptResult]) -> list[dict]:
    """doc 09 §9.4 — aggregate per topic: مدت واقعی و میانگین + درست/غلط."""
    agg: dict[tuple, dict] = {}
    for a in attempts:
        key = (a.topic_id, a.topic_title)
        slot = agg.setdefault(
            key, {"topic_id": a.topic_id, "topic_title": a.topic_title, "attempts": 0, "duration_seconds": 0}
        )
        slot["attempts"] += 1
        slot["duration_seconds"] += a.duration_seconds or 0
    for a in latest.values():
        key = (a.topic_id, a.topic_title)
        slot = agg.setdefault(
            key, {"topic_id": a.topic_id, "topic_title": a.topic_title, "attempts": 0, "duration_seconds": 0}
        )
        slot["correct"] = slot.get("correct", 0) + (1 if a.result == "correct" else 0)
        slot["wrong"] = slot.get("wrong", 0) + (1 if a.result == "wrong" else 0)
    for slot in agg.values():
        slot.setdefault("correct", 0)
        slot.setdefault("wrong", 0)
        n = slot["attempts"] or 1
        slot["avg_seconds"] = round(slot["duration_seconds"] / n, 1)
    return sorted(agg.values(), key=lambda s: (s["topic_title"] or ""))


def _scoring(db, session: TestSession, attempts: list[AttemptResult]) -> dict:
    latest = _latest_by_question(attempts)
    pairs = [(a.status, a.result) for a in latest.values()]
    k = get_penalty_k(db)
    return domain.score_attempts(pairs, session.total_count, k)


def _ensure_error_note(db, student: Student, session: TestSession, attempt: AttemptResult, key: str | None) -> None:
    """دفترچه خطا (پایه) — برای هر attempt غلط یک ردیف؛ تکراری ساخته نمی‌شود."""
    exists = db.execute(
        select(ErrorNote.id).where(ErrorNote.attempt_result_id == attempt.id)
    ).scalar_one_or_none()
    if exists:
        return
    db.add(
        ErrorNote(
            student_id=student.id,
            attempt_result_id=attempt.id,
            question_id=attempt.question_id,
            session_id=session.id,
            topic_id=attempt.topic_id,
            book_title=session.resource_title,
            topic_title=attempt.topic_title,
            question_number=attempt.question_number,
            your_answer=attempt.answer,
            correct_answer=key,
        )
    )


# --- endpoints ------------------------------------------------------------------

def preview(db, student: Student, resource_id, topic_ids, from_number, to_number, parity, count, difficulty) -> dict:
    resource = _owned_resource(db, student, resource_id)
    filtered, scope_count = _select_questions(
        db, resource.id, topic_ids, from_number, to_number, parity, count, difficulty
    )
    numbers = sorted({q.number for q, _ in filtered})
    return {
        "resource_id": resource.id,
        "resource_title": resource.title,
        "available_in_scope": scope_count,
        "matching": len(filtered),
        "numbers": numbers[:300],
        "filters": {
            "topic_ids": topic_ids,
            "from": from_number,
            "to": to_number,
            "parity": parity,
            "count": count,
            "difficulty": difficulty,
        },
        "message": None if filtered else domain.zero_remaining_message(scope_count),
    }


def create_session(db, student: Student, payload) -> dict:
    resource = _owned_resource(db, student, payload.resource_id)

    if payload.topic_ids:
        owned = set(
            db.execute(
                select(Topic.id).where(Topic.resource_id == resource.id, Topic.id.in_(payload.topic_ids))
            ).scalars()
        )
        if len(owned) != len(set(payload.topic_ids)):
            raise HTTPException(status_code=422, detail=MSG_TOPICS_NOT_IN_BOOK)

    if payload.mode == "timed" and not payload.planned_duration:
        raise HTTPException(status_code=422, detail=MSG_TIMED_NEEDS_DURATION)
    if payload.from_number is not None and payload.to_number is not None and payload.from_number > payload.to_number:
        raise HTTPException(status_code=422, detail=MSG_BAD_RANGE)

    filtered, scope_count = _select_questions(
        db,
        resource.id,
        payload.topic_ids,
        payload.from_number,
        payload.to_number,
        payload.parity,
        payload.count,
        payload.difficulty,
    )
    if not filtered:
        # doc 09 §9.2 — خطای اجباری
        raise HTTPException(status_code=422, detail=domain.zero_remaining_message(scope_count))

    session = TestSession(
        student_id=student.id,
        mode=payload.mode,
        resource_id=resource.id,
        resource_title=resource.title,
        label=(payload.label or "").strip() or None,
        source="ui",
        filters={
            "topic_ids": payload.topic_ids,
            "from": payload.from_number,
            "to": payload.to_number,
            "parity": payload.parity,
            "count": payload.count,
            "difficulty": payload.difficulty,
        },
        selected_question_ids=[q.id for q, _ in filtered],
        total_count=len(filtered),
        planned_duration=payload.planned_duration if payload.mode == "timed" else None,
        started_at=_utcnow(),
    )
    db.add(session)
    db.flush()
    return {"session": _session_out(session), "questions": _questions_for_session(db, session, {})}


def add_records(db, student: Student, session_id: str, payload) -> dict:
    session = _load_session(db, student, session_id)
    if session.finished_at is not None:
        # append-only history (FR-T5): بعد از finish نتایج قفل‌اند
        raise HTTPException(status_code=409, detail=MSG_FINISHED_LOCKED)

    q_rows = _questions_by_ids(db, session.selected_question_ids or [])
    by_id = {q.id: (q, t) for q, t in q_rows}
    by_number: dict[int, tuple[Question, Topic]] = {}
    for q, t in q_rows:
        by_number.setdefault(q.number, (q, t))

    now = _utcnow()
    added = 0
    for item in payload.items:
        target = None
        if item.question_id:
            target = by_id.get(item.question_id)
        elif item.number is not None:
            target = by_number.get(item.number)
        else:
            raise HTTPException(status_code=422, detail=MSG_RECORD_NEEDS_TARGET)
        if target is None:
            raise HTTPException(status_code=422, detail=MSG_QUESTION_NOT_IN_SESSION)
        q, t = target

        key, version = _latest_key(db, q.id)
        result = domain.result_for(item.status, item.result, item.answer, key)
        attempt = AttemptResult(
            session_id=session.id,
            student_id=student.id,
            question_id=q.id,
            topic_id=t.id,
            question_number=q.number,
            topic_title=t.title,
            answer=item.answer,
            correct_answer=key,
            answer_key_version=version,
            status=item.status,
            result=result,
            duration_seconds=item.duration_seconds,
            solved_at=now,
        )
        db.add(attempt)
        db.flush()
        added += 1
        if result == "wrong":
            _ensure_error_note(db, student, session, attempt, key)

    event_bus.publish(
        Event(TEST_RECORDS_CREATED, {"student_id": student.id, "session_id": session.id, "count": added})
    )

    attempts = _load_attempts(db, session.id)
    return {"added": added, "progress": _scoring(db, session, attempts)}


def finish_session(db, student: Student, session_id: str, payload) -> dict:
    session = _load_session(db, student, session_id)
    attempts = _load_attempts(db, session.id)

    if session.finished_at is not None:
        # V2-T02 — finish ایدمپوتنت: همان snapshot، بدون بازمحاسبه و بدون رویداد
        return {
            "session": _session_out(session),
            "idempotent": True,
            "topics": _topic_aggregate(session, attempts, _latest_by_question(attempts)),
        }

    sc = _scoring(db, session, attempts)
    session.correct_count = sc["correct_count"]
    session.wrong_count = sc["wrong_count"]
    session.unanswered_count = sc["unanswered_count"]
    session.not_entered_count = sc["not_entered_count"]
    session.percent_konkur = sc["percent_konkur"]
    session.percent_no_penalty = sc["percent_no_penalty"]
    session.penalty_k = sc["penalty_k"]
    session.total_count = sc["total_count"]
    if payload.actual_duration is not None:
        session.actual_duration = payload.actual_duration
    else:
        session.actual_duration = _sum_durations(attempts)
    session.finished_at = _utcnow()
    db.flush()

    # رویداد finish در router و «بعد از commit» publish می‌شود تا مصرف‌کننده
    # (review rebuild — فاز ۴) داده commitشده را ببیند (doc 09 §9.2: finish →
    # scoring + events + learning state update).

    return {
        "session": _session_out(session),
        "idempotent": False,
        "topics": _topic_aggregate(session, attempts, _latest_by_question(attempts)),
    }


def past_import(db, student: Student, payload) -> dict:
    resource = _owned_resource(db, student, payload.resource_id)
    topic = db.execute(
        select(Topic).where(Topic.id == payload.topic_id, Topic.resource_id == resource.id)
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail=MSG_TOPIC_NOT_FOUND)

    label = (payload.label or "").strip() or f"{resource.title} — {topic.title}"
    session = (
        db.execute(
            select(TestSession)
            .where(
                TestSession.student_id == student.id,
                TestSession.mode == "past",
                TestSession.resource_id == resource.id,
                TestSession.label == label,
            )
            .order_by(TestSession.created_at.desc())
            .limit(1)
        )
        .scalars()
        .first()
    )
    created_session = session is None
    if session is None:
        session = TestSession(
            student_id=student.id,
            mode="past",
            resource_id=resource.id,
            resource_title=resource.title,
            label=label,
            source="past-import",
            filters={"topic_id": topic.id, "topic_title": topic.title},
            selected_question_ids=[],
            total_count=0,
            started_at=_utcnow(),
        )
        db.add(session)
        db.flush()

    now = _utcnow()
    imported = updated = created_questions = created_keys = 0
    for item in payload.items:
        q = db.execute(
            select(Question).where(Question.topic_id == topic.id, Question.number == item.number)
        ).scalar_one_or_none()
        if q is None:
            # past import می‌تواند سوال‌های کتاب TOC-only را بسازد (کلید هم می‌آورد)
            q = Question(topic_id=topic.id, number=item.number, difficulty=item.difficulty)
            db.add(q)
            db.flush()
            created_questions += 1
        elif item.difficulty is not None and q.difficulty is None:
            q.difficulty = item.difficulty

        key, version = _latest_key(db, q.id)
        if item.correct_answer is not None and str(item.correct_answer).strip():
            new_key = str(item.correct_answer).strip()
            if key is None or domain.normalize_answer(key) != domain.normalize_answer(new_key):
                # doc 05 — answer_keys نسخه‌دار append-only (تاریخچه کلید بازنویسی نمی‌شود)
                version = (version or 0) + 1
                db.add(AnswerKey(question_id=q.id, answer=new_key, version=version))
                db.flush()
                key, created_keys = new_key, created_keys + 1

        result = domain.result_for(item.status, item.result, item.answer, key)

        # doc 09 §9.3 — تکمیل بعدی «همان attempt» را به answered تبدیل می‌کند (نه duplicate)
        attempt = (
            db.execute(
                select(AttemptResult)
                .where(AttemptResult.session_id == session.id, AttemptResult.question_id == q.id)
                .order_by(AttemptResult.created_at.desc(), AttemptResult.id.desc())
                .limit(1)
            )
            .scalars()
            .first()
        )
        if attempt is None:
            attempt = AttemptResult(
                session_id=session.id,
                student_id=student.id,
                question_id=q.id,
                topic_id=topic.id,
                question_number=q.number,
                topic_title=topic.title,
                status=item.status,
                answer=item.answer,
                duration_seconds=item.duration_seconds,
                solved_at=now,
            )
            db.add(attempt)
            imported += 1
        else:
            attempt.status = item.status
            if item.answer is not None:
                attempt.answer = item.answer
            if item.duration_seconds is not None:
                attempt.duration_seconds = item.duration_seconds
            attempt.solved_at = now
            updated += 1
        attempt.result = result
        attempt.correct_answer = key
        attempt.answer_key_version = version
        db.flush()
        if result == "wrong":
            _ensure_error_note(db, student, session, attempt, key)

    # scoring مجدد در هر import — تکمیل not_entered درصد را به‌روز می‌کند
    attempts = _load_attempts(db, session.id)
    latest = _latest_by_question(attempts)
    session.total_count = len(latest)
    sc = _scoring(db, session, attempts)
    session.correct_count = sc["correct_count"]
    session.wrong_count = sc["wrong_count"]
    session.unanswered_count = sc["unanswered_count"]
    session.not_entered_count = sc["not_entered_count"]
    session.percent_konkur = sc["percent_konkur"]
    session.percent_no_penalty = sc["percent_no_penalty"]
    session.penalty_k = sc["penalty_k"]
    if session.finished_at is None:
        session.finished_at = now
    if session.actual_duration is None:
        session.actual_duration = _sum_durations(attempts)
    db.flush()

    # رویداد past در router بعد از commit publish می‌شود (دید مصرف‌کننده).
    return {
        "session": _session_out(session),
        "created_session": created_session,
        "imported": imported,
        "updated": updated,
        "created_questions": created_questions,
        "created_answer_keys": created_keys,
    }


def list_sessions(db, student: Student, limit: int = 50) -> list[dict]:
    rows = (
        db.execute(
            select(TestSession)
            .where(TestSession.student_id == student.id)
            .order_by(TestSession.started_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_session_out(s) for s in rows]


def get_session(db, student: Student, session_id: str) -> dict:
    session = _load_session(db, student, session_id)
    attempts = _load_attempts(db, session.id)
    latest = _latest_by_question(attempts)
    return {
        "session": _session_out(session),
        "questions": _questions_for_session(db, session, latest),
        "attempts": [_attempt_out(a) for a in attempts],  # تاریخچه کامل append-only
        "topics": _topic_aggregate(session, attempts, latest),
    }


def list_error_notes(db, student: Student, limit: int = 200) -> list[dict]:
    rows = (
        db.execute(
            select(ErrorNote)
            .where(ErrorNote.student_id == student.id)
            .order_by(ErrorNote.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_note_out(n) for n in rows]


def update_error_note(db, student: Student, note_id: str, payload) -> dict:
    note = db.execute(
        select(ErrorNote).where(ErrorNote.id == note_id, ErrorNote.student_id == student.id)
    ).scalar_one_or_none()
    if note is None:
        raise HTTPException(status_code=404, detail=MSG_NOTE_NOT_FOUND)
    data = payload.model_dump(exclude_unset=True)
    if "error_type" in data:
        note.error_type = data["error_type"]
    if "note" in data:
        note.note = data["note"]
    note.updated_at = _utcnow()
    db.flush()
    return _note_out(note)


def _note_out(n: ErrorNote) -> dict:
    return {
        "id": n.id,
        "session_id": n.session_id,
        "question_id": n.question_id,
        "book_title": n.book_title,
        "topic_title": n.topic_title,
        "question_number": n.question_number,
        "your_answer": n.your_answer,
        "correct_answer": n.correct_answer,
        "error_type": n.error_type,
        "error_type_fa": domain.ERROR_TYPE_LABELS_FA.get(n.error_type) if n.error_type else None,
        "note": n.note,
        "created_at": _iso(n.created_at),
    }


# --- تیک‌ها (doc 04 Question Marking، doc 08 §8.4، doc 10 §10.1) -------------------

MSG_QUESTION_NOT_FOUND = "سوال پیدا نشد."


def _owned_question(db, student: Student, question_id: str) -> Question:
    q = db.execute(
        select(Question)
        .join(Topic, Topic.id == Question.topic_id)
        .join(Resource, Resource.id == Topic.resource_id)
        .where(Question.id == question_id, Resource.student_id == student.id)
    ).scalar_one_or_none()
    if q is None:
        raise HTTPException(status_code=404, detail=MSG_QUESTION_NOT_FOUND)
    return q


def _marks_out(mark, question_id: str) -> dict:
    return {
        "question_id": question_id,
        "review": bool(mark.review) if mark else False,
        "important": bool(mark.important) if mark else False,
        "hard": bool(mark.hard) if mark else False,
        "updated_at": _iso(mark.updated_at) if mark else None,
    }


def get_marks(db, student: Student, question_id: str) -> dict:
    _owned_question(db, student, question_id)
    mark = db.execute(
        select(QuestionMark).where(
            QuestionMark.student_id == student.id, QuestionMark.question_id == question_id
        )
    ).scalar_one_or_none()
    return _marks_out(mark, question_id)


def put_marks(db, student: Student, question_id: str, payload) -> dict:
    """تیک review/important/hard → ورود به صف مرور (doc 10 §10.1) + رویداد."""
    from app.modules.review.service import sync_marks_into_queue  # service→service (doc 03 §3.1)

    _owned_question(db, student, question_id)
    mark = db.execute(
        select(QuestionMark).where(
            QuestionMark.student_id == student.id, QuestionMark.question_id == question_id
        )
    ).scalar_one_or_none()
    if mark is None:
        mark = QuestionMark(student_id=student.id, question_id=question_id)
        db.add(mark)
    data = payload.model_dump(exclude_unset=True)
    for f in ("review", "important", "hard"):
        if f in data and data[f] is not None:
            setattr(mark, f, bool(data[f]))
    mark.updated_at = _utcnow()
    db.flush()

    event_bus.publish(
        Event(
            QUESTION_MARKS_CHANGED,
            {
                "student_id": student.id,
                "question_id": question_id,
                "review": mark.review,
                "important": mark.important,
                "hard": mark.hard,
            },
        )
    )
    sync_marks_into_queue(db, student, question_id, mark)
    db.flush()
    return _marks_out(mark, question_id)
