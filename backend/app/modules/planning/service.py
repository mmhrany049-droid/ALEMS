"""Planning & Capacity & Today Hub — application services (doc 03 §3.1، doc 11).

capacity از time blocks + school override + completion هفت روز + state (doc 11.2)،
generate-week با pipeline دوازده‌مرحله‌ای لاگ‌شده (doc 11.3)، manual override
(doc 11.4: locked در regenerate حفظ می‌شود — V2-P03)، recovery بدون dump روی
فردا (doc 11.5 — V2-P04)، GET /today کامل (doc 11.1) و recommendation با
reason code فارسی (doc 08 §8.10).
"""
from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

from fastapi.exceptions import HTTPException
from sqlalchemy import case, delete, func, select

from app.core.events import PLAN_UPDATED, Event, event_bus
from app.core.jalali import (
    JalaliDate,
    gregorian_to_jalali,
    jalali_to_gregorian,
    jalali_weekday,
    today_jalali,
    week_start as jalali_week_start,
)
from app.modules.academic.models import Resource, Topic
from app.modules.activity.models import AttemptResult
from app.modules.exam import domain as exam_domain
from app.modules.exam.models import Exam
from app.modules.planning import domain
from app.modules.planning.models import (
    CapacitySnapshot,
    Goal,
    PlanRun,
    PlanTask,
    PrioritySnapshot,
    Recommendation,
    TimeBlock,
)
from app.modules.review.models import LearningState, ReviewItem
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Checkin, Student, TaughtTopic
from app.modules.student.schemas import StateOut
from app.modules.student.service import get_state as student_get_state

logger = logging.getLogger("alems.planner")

MSG_INVALID_DATE = "تاریخ نامعتبر است."
MSG_TASK_NOT_FOUND = "کار برنامه پیدا نشد."
MSG_BAD_TIME = "زمان را مثل ۰۸:۳۰ وارد کن."
MSG_END_BEFORE_START = "ساعت پایان باید بعد از شروع باشد."
MSG_SPLIT_PARTS = "تقسیم باید حداقل دو بخش ۱۰ دقیقه‌ای باشد."
MSG_MERGE_COUNT = "برای ادغام حداقل دو کار هم‌روز انتخاب کن."
MSG_MERGE_DAYS = "فقط کارهای یک روز با هم ادغام می‌شوند."
MSG_OVERRIDE_BLOCKS = "برای روز مدرسه‌ای، بلوک‌های مدرسه را وارد کن یا تعطیلی را ثبت کن."
MSG_NO_REMAINING_DAYS = "روز باقی‌مانده‌ای در این هفته نیست."
MSG_REC_NOT_FOUND = "پیشنهاد پیدا نشد."
MSG_GOAL_TITLE = "عنوان هدف نمی‌تواند خالی باشد."
MSG_TASK_TITLE = "عنوان کار نمی‌تواند خالی باشد."

WEEKDAYS_FA = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
KIND_LABELS_FA = {"study": "مطالعه", "test": "تست", "review": "مرور", "goal": "هدف"}
SOURCE_LABELS_FA = {"generated": "پیشنهاد سیستم", "manual": "دستی", "recovered": "جبرانی"}

_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _today() -> dt.date:
    return today_jalali().to_gregorian()


def _iso(d: dt.date | None) -> str | None:
    return d.isoformat() if d else None


def _jalali(d: dt.date | None) -> JalaliDate | None:
    return JalaliDate(*gregorian_to_jalali(d.year, d.month, d.day)) if d else None


def _jalali_str(d: dt.date | None) -> str | None:
    j = _jalali(d)
    return j.format() if j else None


def _weekday(d: dt.date) -> int:
    j = _jalali(d)
    return jalali_weekday(j.year, j.month, j.day) if j else 0


def _weekday_fa(d: dt.date) -> str:
    return WEEKDAYS_FA[_weekday(d)]


def parse_date(raw: str) -> dt.date:
    """شمسی «1405/06/29» یا «1405-06-29» یا میلادی «2026-09-20»."""
    s = (raw or "").strip().translate(_FA_DIGITS)
    parts = s.replace("/", "-").split("-")
    if len(parts) != 3:
        raise HTTPException(status_code=422, detail=MSG_INVALID_DATE)
    try:
        a, b, c = (int(p) for p in parts)
    except ValueError:
        raise HTTPException(status_code=422, detail=MSG_INVALID_DATE) from None
    try:
        if a < 1500:  # سال شمسی (۱۳۰۰–۱۴۹۹) — میلادی‌ها ≥ ۱۵۰۰
            return dt.date(*jalali_to_gregorian(a, b, c))
        return dt.date(a, b, c)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail=MSG_INVALID_DATE) from None


def _to_minutes(v: Any) -> int:
    if isinstance(v, bool):
        raise HTTPException(status_code=422, detail=MSG_BAD_TIME)
    if isinstance(v, int):
        m = v
    else:
        s = str(v).strip().translate(_FA_DIGITS)
        if ":" not in s:
            raise HTTPException(status_code=422, detail=MSG_BAD_TIME)
        hh, _, mm = s.partition(":")
        try:
            m = int(hh) * 60 + int(mm or 0)
        except ValueError:
            raise HTTPException(status_code=422, detail=MSG_BAD_TIME) from None
    if not (0 <= m < 1440):
        raise HTTPException(status_code=422, detail=MSG_BAD_TIME)
    return m


def hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def week_of(d: dt.date) -> tuple[dt.date, list[dt.date]]:
    """شنبه تا جمعه هفته‌ای که d در آن است (قاعدة ثابت تقویم)."""
    j = _jalali(d)
    ws_j = jalali_week_start(j)
    ws = ws_j.to_gregorian()
    return ws, [ws + dt.timedelta(days=i) for i in range(7)]


# --- time blocks (doc 11.2) ----------------------------------------------------------------

def _block_out(b: TimeBlock) -> dict:
    return {
        "id": b.id,
        "date": _iso(b.date),
        "kind": b.kind,
        "start": hhmm(b.start_minutes),
        "end": hhmm(b.end_minutes),
        "start_minutes": b.start_minutes,
        "end_minutes": b.end_minutes,
        "minutes": b.end_minutes - b.start_minutes,
        "title": b.title,
        "source": b.source,
    }


def list_blocks(db, student: Student, date: dt.date) -> list[dict]:
    rows = (
        db.execute(
            select(TimeBlock)
            .where(TimeBlock.student_id == student.id, TimeBlock.date == date)
            .order_by(TimeBlock.start_minutes)
        )
        .scalars()
        .all()
    )
    return [_block_out(b) for b in rows]


def put_blocks(db, student: Student, date: dt.date, blocks: list) -> dict:
    parsed: list[dict] = []
    for b in blocks:
        kind = (b.kind or "").strip()
        if kind not in ("school", "class", "free"):
            raise HTTPException(status_code=422, detail="نوع بلوک باید school یا class یا free باشد.")
        start = _to_minutes(b.start)
        end = _to_minutes(b.end)
        if end <= start:
            raise HTTPException(status_code=422, detail=MSG_END_BEFORE_START)
        parsed.append({"kind": kind, "start_minutes": start, "end_minutes": end, "title": b.title})

    db.execute(delete(TimeBlock).where(TimeBlock.student_id == student.id, TimeBlock.date == date))
    now = _utcnow()
    for p in parsed:
        db.add(
            TimeBlock(
                student_id=student.id,
                date=date,
                kind=p["kind"],
                start_minutes=p["start_minutes"],
                end_minutes=p["end_minutes"],
                title=p["title"],
                source="schedule",
                created_at=now,
                updated_at=now,
            )
        )
    db.flush()
    cap = _capacity(db, student, date, force=True, source="computed")
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "date": _iso(date), "blocks": len(parsed)}))
    return {"date": _iso(date), "date_jalali": _jalali_str(date), "blocks": list_blocks(db, student, date), "capacity": cap}


def school_override(db, student: Student, date: dt.date, school_off: bool, blocks: list) -> dict:
    """V2-P02 — override همان روز ظرفیت را بازمحاسبه می‌کند (doc 08 §8.6)."""
    parsed: list[dict] = []
    if not school_off:
        if not blocks:
            raise HTTPException(status_code=422, detail=MSG_OVERRIDE_BLOCKS)
        for b in blocks:
            start = _to_minutes(b.start)
            end = _to_minutes(b.end)
            if end <= start:
                raise HTTPException(status_code=422, detail=MSG_END_BEFORE_START)
            parsed.append({"start_minutes": start, "end_minutes": end, "title": b.title})

    db.execute(
        delete(TimeBlock).where(
            TimeBlock.student_id == student.id, TimeBlock.date == date, TimeBlock.kind == "school"
        )
    )
    now = _utcnow()
    for p in parsed:
        db.add(
            TimeBlock(
                student_id=student.id,
                date=date,
                kind="school",
                start_minutes=p["start_minutes"],
                end_minutes=p["end_minutes"],
                title=p["title"] or "مدرسه",
                source="override",
                created_at=now,
                updated_at=now,
            )
        )
    db.flush()
    cap = _capacity(db, student, date, force=True, source="override")
    event_bus.publish(
        Event(PLAN_UPDATED, {"student_id": student.id, "date": _iso(date), "school_override": True, "school_off": school_off})
    )
    return {
        "date": _iso(date),
        "date_jalali": _jalali_str(date),
        "school_off": school_off,
        "blocks": [b for b in list_blocks(db, student, date) if b["kind"] == "school"],
        "capacity": cap,
    }


# --- capacity (doc 11.2) -------------------------------------------------------------------

def _completion_7d(db, student_id: str, date: dt.date) -> tuple[int, int]:
    """میانگین انجام ۷ روز اخیر — فقط سابقه‌ی واقعی.

    کار دستی/قفل‌شده تعهد دانش‌آموز است و همیشه شمرده می‌شود؛ کار پیشنهادی
    (generated) که هنوز pending مانده «انجام‌نشده» حساب نمی‌شود — برنامه
    پیشنهاد است (doc 08 §8.7) و واردنشده ≠ بی‌پاسخ. در غیر این صورت
    خودِ planner با پیشنهاد دیروز، ظرفیت کل هفته را صفر می‌کرد.
    """
    start = date - dt.timedelta(days=7)
    rows = db.execute(
        select(PlanTask.status, PlanTask.source).where(
            PlanTask.student_id == student_id, PlanTask.date >= start, PlanTask.date < date
        )
    ).all()
    kept = [(status, src) for status, src in rows if src != "generated" or status != "pending"]
    total = len(kept)
    done = sum(1 for status, _src in kept if status == "done")
    return done, total


def _capacity(db, student: Student, date: dt.date, force: bool = False, source: str = "computed") -> dict:
    row = db.execute(
        select(CapacitySnapshot).where(CapacitySnapshot.student_id == student.id, CapacitySnapshot.date == date)
    ).scalar_one_or_none()
    if row is not None and not force:
        source = row.source

    blocks = [
        {"kind": b.kind, "start_minutes": b.start_minutes, "end_minutes": b.end_minutes}
        for b in db.execute(
            select(TimeBlock).where(TimeBlock.student_id == student.id, TimeBlock.date == date)
        ).scalars().all()
    ]
    avail = domain.day_availability(blocks)
    done, total = _completion_7d(db, student.id, date)

    energy = focus = None
    chk = db.execute(
        select(Checkin).where(Checkin.student_id == student.id, Checkin.date == date)
    ).scalar_one_or_none()
    if chk is not None:
        energy, focus = chk.energy, chk.focus

    cap = domain.compute_capacity(
        free_minutes=avail["free_minutes"],
        weekday=_weekday(date),
        has_blocks=avail["has_blocks"],
        done_7d=done,
        total_7d=total,
        energy=energy,
        focus=focus,
    )

    now = _utcnow()
    if row is None:
        row = CapacitySnapshot(student_id=student.id, date=date, created_at=now)
        db.add(row)
    row.school_minutes = avail["school_minutes"]
    row.class_minutes = avail["class_minutes"]
    row.available_study_minutes = cap["available_minutes"]
    row.estimated_capacity_tasks = cap["suggested_task_count"]
    row.suggested_session_count = cap["suggested_session_count"]
    row.completion_rate = cap["completion_rate"]
    row.source = source
    row.updated_at = now
    db.flush()

    return {
        "date": _iso(date),
        "date_jalali": _jalali_str(date),
        "weekday_fa": _weekday_fa(date),
        "school_minutes": avail["school_minutes"],
        "class_minutes": avail["class_minutes"],
        "free_minutes": avail["free_minutes"],
        "has_blocks": avail["has_blocks"],
        "available_minutes": cap["available_minutes"],
        "suggested_task_count": cap["suggested_task_count"],
        "suggested_session_count": cap["suggested_session_count"],
        "completion_rate": cap["completion_rate"],
        "state_factor": cap["state_factor"],
        "source": source,
    }


def get_capacity(db, student: Student, date: dt.date) -> dict:
    return _capacity(db, student, date, force=False)


# --- plans (doc 11.4) -------------------------------------------------------------------------

def _task_out(t: PlanTask) -> dict:
    return {
        "id": t.id,
        "date": _iso(t.date),
        "date_jalali": _jalali_str(t.date),
        "kind": t.kind,
        "kind_fa": KIND_LABELS_FA.get(t.kind, t.kind),
        "title": t.title,
        "topic_id": t.topic_id,
        "topic_title": t.topic_title,
        "book_title": t.book_title,
        "minutes": t.minutes,
        "count": t.count,
        "status": t.status,
        "locked": bool(t.locked),
        "source": t.source,
        "source_fa": SOURCE_LABELS_FA.get(t.source, t.source),
        "reason_code": t.reason_code,
        "reason_fa": domain.reason_fa(t.reason_code) if t.reason_code else None,
        "order_index": t.order_index,
    }


def _day_tasks(db, student_id: str, date: dt.date) -> list[PlanTask]:
    return (
        db.execute(
            select(PlanTask)
            .where(PlanTask.student_id == student_id, PlanTask.date == date)
            .order_by(PlanTask.order_index, PlanTask.created_at)
        )
        .scalars()
        .all()
    )


def get_plan(db, student: Student, date: dt.date) -> dict:
    tasks = _day_tasks(db, student.id, date)
    cap = get_capacity(db, student, date)
    return {
        "date": _iso(date),
        "date_jalali": _jalali_str(date),
        "weekday_fa": _weekday_fa(date),
        "capacity": cap,
        "tasks": [_task_out(t) for t in tasks],
        "counts": {
            "total": len(tasks),
            "done": sum(1 for t in tasks if t.status == "done"),
            "locked": sum(1 for t in tasks if t.locked),
            "minutes": sum(t.minutes for t in tasks),
        },
    }


def _load_task(db, student: Student, task_id: str) -> PlanTask:
    t = db.execute(
        select(PlanTask).where(PlanTask.id == task_id, PlanTask.student_id == student.id)
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=404, detail=MSG_TASK_NOT_FOUND)
    return t


def _topic_meta(db, topic_id: str | None) -> tuple[str | None, str | None]:
    if not topic_id:
        return None, None
    row = db.execute(
        select(Topic.title, Resource.title)
        .join(Resource, Resource.id == Topic.resource_id)
        .where(Topic.id == topic_id)
    ).first()
    return (row[0], row[1]) if row else (None, None)


def put_plan(db, student: Student, date: dt.date, items: list) -> dict:
    """ویرایش دستی روز — «ویرایش دستی همیشه برنده است» (doc 08 §8.7).

    id داشته باشد → update؛ نداشته باشد → افزودن (source=manual)؛
    taskهای موجودی که در لیست نیستند حذف می‌شوند (حتی locked — کاربر صریح خواسته).
    """
    existing = {t.id: t for t in _day_tasks(db, student.id, date)}
    keep_ids: set[str] = set()
    now = _utcnow()
    ws, _days = week_of(date)
    order = 0

    for it in items:
        order += 1
        if it.id:
            t = existing.get(it.id)
            if t is None:
                raise HTTPException(status_code=404, detail=MSG_TASK_NOT_FOUND)
            keep_ids.add(t.id)
            if it.title is not None and it.title.strip():
                t.title = it.title.strip()[:200]
            if it.kind is not None:
                if it.kind not in KIND_LABELS_FA:
                    raise HTTPException(status_code=422, detail="نوع کار نامعتبر است.")
                t.kind = it.kind
            if it.minutes is not None:
                if it.minutes <= 0:
                    raise HTTPException(status_code=422, detail="مدت کار باید مثبت باشد.")
                t.minutes = it.minutes
            if it.count is not None:
                t.count = it.count
            if it.status is not None:
                if it.status not in ("pending", "done", "skipped"):
                    raise HTTPException(status_code=422, detail="وضعیت کار نامعتبر است.")
                t.status = it.status
            if it.locked is not None:
                t.locked = bool(it.locked)
            if it.topic_id is not None:
                t.topic_id = it.topic_id or None
                t.topic_title, t.book_title = _topic_meta(db, t.topic_id)
            t.order_index = order
            t.updated_at = now
        else:
            title = (it.title or "").strip()
            if not title:
                raise HTTPException(status_code=422, detail=MSG_TASK_TITLE)
            minutes = it.minutes if it.minutes and it.minutes > 0 else domain.AVG_TASK_MINUTES
            topic_title, book_title = _topic_meta(db, it.topic_id)
            db.add(
                PlanTask(
                    student_id=student.id,
                    date=date,
                    week_start=ws,
                    kind=it.kind if it.kind in KIND_LABELS_FA else "study",
                    topic_id=it.topic_id or None,
                    topic_title=topic_title,
                    book_title=book_title,
                    title=title[:200],
                    minutes=minutes,
                    count=it.count,
                    status=it.status if it.status in ("pending", "done", "skipped") else "pending",
                    locked=bool(it.locked),
                    source="manual",
                    reason_code=it.reason_code,
                    order_index=order,
                    created_at=now,
                    updated_at=now,
                )
            )

    removed = 0
    for tid, t in existing.items():
        if tid not in keep_ids:
            db.delete(t)
            removed += 1
    db.flush()

    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "date": _iso(date), "manual": True}))
    return get_plan(db, student, date) | {"removed": removed}


def move_task(db, student: Student, task_id: str, to_date: dt.date) -> dict:
    t = _load_task(db, student, task_id)
    ws, _days = week_of(to_date)
    t.date = to_date
    t.week_start = ws
    if t.source == "generated":
        t.source = "manual"  # دستی جابه‌جا شده — در regenerate محفوظ است
    t.updated_at = _utcnow()
    db.flush()
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "task_id": task_id, "moved": _iso(to_date)}))
    return _task_out(t)


def split_task(db, student: Student, task_id: str, parts: list[int]) -> dict:
    t = _load_task(db, student, task_id)
    parts = [int(p) for p in parts]
    if len(parts) < 2 or any(p < 10 for p in parts):
        raise HTTPException(status_code=422, detail=MSG_SPLIT_PARTS)
    now = _utcnow()
    total = len(parts)
    base_title = t.title
    t.minutes = parts[0]
    t.title = f"{base_title} ({1}/{total})"
    t.source = "manual" if t.source == "generated" else t.source
    t.updated_at = now
    created = [t]
    for i, p in enumerate(parts[1:], start=2):
        nt = PlanTask(
            student_id=t.student_id,
            date=t.date,
            week_start=t.week_start,
            kind=t.kind,
            topic_id=t.topic_id,
            topic_title=t.topic_title,
            book_title=t.book_title,
            title=f"{base_title} ({i}/{total})",
            minutes=p,
            count=None,
            status="pending",
            locked=False,  # قفل فقط روی بخش اول می‌ماند
            source="manual",
            reason_code=t.reason_code,
            order_index=t.order_index + i - 1,
            created_at=now,
            updated_at=now,
        )
        db.add(nt)
        created.append(nt)
    db.flush()
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "task_id": task_id, "split": total}))
    return {"parts": total, "tasks": [_task_out(x) for x in created]}


def merge_tasks(db, student: Student, task_ids: list[str]) -> dict:
    ids = list(dict.fromkeys(task_ids))
    if len(ids) < 2:
        raise HTTPException(status_code=422, detail=MSG_MERGE_COUNT)
    tasks = [_load_task(db, student, tid) for tid in ids]
    if len({t.date for t in tasks}) != 1:
        raise HTTPException(status_code=422, detail=MSG_MERGE_DAYS)
    tasks.sort(key=lambda t: t.order_index)
    first = tasks[0]
    first.minutes = sum(t.minutes for t in tasks)
    counts = [t.count for t in tasks if t.count]
    first.count = sum(counts) if counts else None
    first.title = " + ".join(t.title for t in tasks)[:200]
    first.locked = any(t.locked for t in tasks)
    first.source = "manual" if first.source == "generated" else first.source
    first.updated_at = _utcnow()
    for t in tasks[1:]:
        db.delete(t)
    db.flush()
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "merged": ids}))
    return _task_out(first)


def set_task_status(db, student: Student, task_id: str, status: str) -> dict:
    """checkbox امروز — سبک‌تر از PUT کل روز."""
    if status not in ("pending", "done", "skipped"):
        raise HTTPException(status_code=422, detail="وضعیت کار نامعتبر است.")
    t = _load_task(db, student, task_id)
    t.status = status
    t.updated_at = _utcnow()
    db.flush()
    # رویداد PLAN_UPDATED(status) در router و «بعد از commit» publish می‌شود (rewards consumer)
    return _task_out(t)


def set_task_lock(db, student: Student, task_id: str, locked: bool) -> dict:
    t = _load_task(db, student, task_id)
    t.locked = bool(locked)
    if t.source == "generated":
        t.source = "manual"  # pin/lock = دستی (doc 11.4)
    t.updated_at = _utcnow()
    db.flush()
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "task_id": task_id, "locked": t.locked}))
    return _task_out(t)


# --- generate week (doc 11.3) ------------------------------------------------------------------

def _priority_items(
    db, student: Student, week_days: list[dt.date], taught_ids: set[str],
    exam_topics: set[str] | None = None,
) -> list[dict]:
    ws_date = week_days[0]
    we_date = week_days[-1]
    states = {
        s.topic_id: s
        for s in db.execute(select(LearningState).where(LearningState.student_id == student.id)).scalars().all()
    }
    review_rows = db.execute(
        select(ReviewItem.topic_id, func.count())
        .where(
            ReviewItem.student_id == student.id,
            ReviewItem.status != "absorbed",
            ReviewItem.scheduled_date >= ws_date,
            ReviewItem.scheduled_date <= we_date,
        )
        .group_by(ReviewItem.topic_id)
    ).all()
    review_by_topic = {tid: int(n) for tid, n in review_rows if tid}

    candidates = (set(states.keys()) | set(review_by_topic.keys())) & taught_ids
    exam_topics = exam_topics or set()
    items: list[dict] = []
    for tid in candidates:
        st = states.get(tid)
        topic_title, book_title = _topic_meta(db, tid)
        readiness = st.exam_readiness if st else 0.5
        weakness = bool(st.weakness) if st else False
        due = review_by_topic.get(tid, 0)
        score = domain.priority_score(readiness, weakness, due)
        reasons = domain.priority_reason_codes(readiness, weakness, due)
        if tid in exam_topics:
            # آزمون نزدیک روی این موضوع — boost ملایم + دلیل exam_prep (doc 11.3 مرحله ۲)
            score = round(score + 0.2, 4)
            if "exam_prep" not in reasons:
                reasons.append("exam_prep")
        items.append(
            {
                "topic_id": tid,
                "topic_title": topic_title or "—",
                "book_title": book_title,
                "score": score,
                "reason_codes": reasons,
                "review_due": due,
                "exam_readiness": round(readiness, 3),
                "weakness": weakness,
            }
        )
    items.sort(key=lambda x: (-x["score"], x["topic_title"]))
    return items[:6]


def generate_week(db, student: Student, week_start_raw: str | None = None) -> dict:
    """pipeline دوازده‌مرحله‌ای ثابت — هر مرحله لاگ می‌شود (doc 11.3)."""
    t0_all = time.perf_counter()
    steps: list[dict] = []

    def step(name: str, started: float, **info: Any) -> None:
        ms = (time.perf_counter() - started) * 1000.0
        steps.append({"step": name, "ms": round(ms, 1), "info": info})
        logger.info("planner step=%s ms=%.1f info=%s", name, ms, info)

    # 1) load context
    t0 = time.perf_counter()
    if week_start_raw:
        anchor = parse_date(week_start_raw)
    else:
        anchor = _today()
    ws, days = week_of(anchor)
    settings = get_settings_map(db)
    max_daily_review = settings["max_daily_review"]
    step("load_context", t0, week_start=_iso(ws), days=7, max_daily_review=max_daily_review)

    # 2) exams — آزمون‌های هفته و ۱۴ روز آینده (doc 11.3 مرحله ۲، doc 12 §12.2)
    t0 = time.perf_counter()
    exam_rows = db.execute(
        select(Exam).where(
            Exam.student_id == student.id,
            Exam.status.in_(["planned", "in_progress"]),
            Exam.scheduled_date.is_not(None),
            Exam.scheduled_date >= ws,
            Exam.scheduled_date <= days[-1] + dt.timedelta(days=7),
        )
    ).scalars().all()
    exam_topics: set[str] = set()
    for e in exam_rows:
        exam_topics.update(e.planned_topic_ids or [])
    step("exams", t0, upcoming=len(exam_rows), exam_topics=len(exam_topics))

    # 3) goals
    t0 = time.perf_counter()
    goals = (
        db.execute(
            select(Goal).where(
                Goal.student_id == student.id,
                (Goal.target_date.is_(None)) | (Goal.target_date.between(ws, days[-1])),
            )
        )
        .scalars()
        .all()
    )
    step("goals", t0, count=len(goals))

    # 4) taught filter (doc 08 §8.8 — practice فقط روی taught)
    t0 = time.perf_counter()
    taught_ids = set(
        db.execute(
            select(TaughtTopic.topic_id).where(
                TaughtTopic.student_id == student.id, TaughtTopic.taught.is_(True)
            )
        ).scalars().all()
    )
    step("taught_filter", t0, taught_topics=len(taught_ids))

    # 5) learning states
    t0 = time.perf_counter()
    states_count = int(
        db.execute(
            select(func.count()).select_from(LearningState).where(LearningState.student_id == student.id)
        ).scalar_one()
    )
    step("learning_states", t0, count=states_count)

    # 6) review demand — سررسیدهای داخل هفته
    t0 = time.perf_counter()
    review_rows = db.execute(
        select(
            ReviewItem.scheduled_date,
            func.count(),
            func.sum(case((ReviewItem.critical.is_(True), 1), else_=0)),
        )
        .where(
            ReviewItem.student_id == student.id,
            ReviewItem.status != "absorbed",
            ReviewItem.scheduled_date >= ws,
            ReviewItem.scheduled_date <= days[-1],
        )
        .group_by(ReviewItem.scheduled_date)
    ).all()
    review_demand = {
        r[0].isoformat(): {"count": int(r[1]), "critical": int(r[2] or 0) > 0} for r in review_rows
    }
    step("review_demand", t0, days_with_demand=len(review_demand), items=sum(v["count"] for v in review_demand.values()))

    # 7) priority items
    t0 = time.perf_counter()
    priority = _priority_items(db, student, days, taught_ids, exam_topics=exam_topics)
    now = _utcnow()
    snap = db.execute(
        select(PrioritySnapshot).where(PrioritySnapshot.student_id == student.id, PrioritySnapshot.week_start == ws)
    ).scalar_one_or_none()
    if snap is None:
        snap = PrioritySnapshot(student_id=student.id, week_start=ws, created_at=now)
        db.add(snap)
    snap.items = priority
    step("priority_items", t0, count=len(priority))

    # 8) capacity per day — override ذخیره‌شده دست‌نخورده می‌ماند
    t0 = time.perf_counter()
    week_days: list[dict] = []
    for d in days:
        cap_row = db.execute(
            select(CapacitySnapshot).where(CapacitySnapshot.student_id == student.id, CapacitySnapshot.date == d)
        ).scalar_one_or_none()
        if cap_row is not None and cap_row.source == "override":
            cap = {
                "available_minutes": cap_row.available_study_minutes,
                "suggested_task_count": cap_row.estimated_capacity_tasks,
                "source": "override",
            }
        else:
            cap = _capacity(db, student, d, force=True, source="computed")
        locked = db.execute(
            select(func.count(), func.coalesce(func.sum(PlanTask.minutes), 0)).where(
                PlanTask.student_id == student.id, PlanTask.date == d, PlanTask.locked.is_(True)
            )
        ).first()
        week_days.append(
            {
                "date": d.isoformat(),
                "weekday": _weekday(d),
                "available_minutes": cap["available_minutes"],
                "suggested_task_count": cap["suggested_task_count"],
                "locked_count": int(locked[0] or 0),
                "locked_minutes": int(locked[1] or 0),
                "source": cap.get("source", "computed"),
            }
        )
    step("capacity_per_day", t0, total_minutes=sum(w["available_minutes"] for w in week_days))

    # 9) allocate tasks
    t0 = time.perf_counter()
    alloc = domain.allocate_week(week_days, review_demand, priority, max_daily_review)
    step("allocate_tasks", t0, allocated=len(alloc))

    # 10) overload check
    t0 = time.perf_counter()
    final: list[dict] = []
    trimmed_total = 0
    by_day: dict[str, list[dict]] = {}
    for a in alloc:
        by_day.setdefault(a["date"], []).append(a)
    caps = {w["date"]: w for w in week_days}
    for d_iso, tasks in by_day.items():
        cap = caps[d_iso]
        keep, trimmed = domain.overload_trim(
            tasks,
            task_cap=cap["suggested_task_count"] - cap["locked_count"],
            available_minutes=cap["available_minutes"] - cap["locked_minutes"],
        )
        trimmed_total += len(trimmed)
        final.extend(keep)
    step("overload_check", t0, trimmed=trimmed_total)

    # 11) explain
    t0 = time.perf_counter()
    for a in final:
        a["reason_fa"] = domain.reason_fa(a["reason_code"])
    step("explain", t0, explained=len(final))

    # 12) save as suggested (نه locked) — V2-P03: locked/manualها حذف نمی‌شوند
    t0 = time.perf_counter()
    removed = int(
        db.execute(
            delete(PlanTask).where(
                PlanTask.student_id == student.id,
                PlanTask.week_start == ws,
                PlanTask.source == "generated",
                PlanTask.locked.is_(False),
            )
        ).rowcount
    )
    kept_locked = int(
        db.execute(
            select(func.count()).select_from(PlanTask).where(
                PlanTask.student_id == student.id, PlanTask.week_start == ws, PlanTask.locked.is_(True)
            )
        ).scalar_one()
    )
    counters: dict[str, int] = {}
    for a in sorted(final, key=lambda x: (x["date"], 0 if x["kind"] == "review" else 1)):
        d = dt.date.fromisoformat(a["date"])
        counters[a["date"]] = counters.get(a["date"], 0) + 1
        db.add(
            PlanTask(
                student_id=student.id,
                date=d,
                week_start=ws,
                kind=a["kind"],
                topic_id=a["topic_id"],
                topic_title=a["topic_title"],
                book_title=a["book_title"],
                title=a["title"],
                minutes=a["minutes"],
                count=a.get("count"),
                status="pending",
                locked=False,  # suggested نه locked (doc 11.3 مرحله ۱۲)
                source="generated",
                reason_code=a["reason_code"],
                order_index=counters[a["date"]],
                created_at=now,
                updated_at=now,
            )
        )
    run = PlanRun(
        student_id=student.id,
        week_start=ws,
        status="ok" if taught_ids or review_demand else "partial",
        steps=steps,
        created_count=len(final),
        kept_locked_count=kept_locked,
        removed_count=removed,
        created_at=now,
    )
    db.add(run)
    db.flush()
    step("save_suggested", t0, created=len(final), removed=removed, kept_locked=kept_locked)

    event_bus.publish(
        Event(PLAN_UPDATED, {"student_id": student.id, "week_start": _iso(ws), "generated": True})
    )

    days_out = []
    for w in week_days:
        d = dt.date.fromisoformat(w["date"])
        day_tasks = _day_tasks(db, student.id, d)
        days_out.append(
            {
                "date": w["date"],
                "date_jalali": _jalali_str(d),
                "weekday_fa": WEEKDAYS_FA[w["weekday"]],
                "available_minutes": w["available_minutes"],
                "suggested_task_count": w["suggested_task_count"],
                "capacity_source": w["source"],
                "tasks_count": len(day_tasks),
                "minutes": sum(t.minutes for t in day_tasks),
            }
        )

    logger.info(
        "planner done week_start=%s created=%d removed=%d kept_locked=%d total_ms=%.1f",
        _iso(ws), len(final), removed, kept_locked, (time.perf_counter() - t0_all) * 1000.0,
    )
    return {
        "week_start": _iso(ws),
        "week_start_jalali": _jalali_str(ws),
        "days": days_out,
        "created": len(final),
        "removed": removed,
        "kept_locked": kept_locked,
        "priority": priority,
        "steps": steps,
        "run_id": run.id,
        "total_ms": round((time.perf_counter() - t0_all) * 1000.0, 1),
    }


# --- recovery (doc 11.5 — بدون dump روی فردا) ---------------------------------------------------

def recover_week(db, student: Student, date_raw: str | None = None) -> dict:
    today = parse_date(date_raw) if date_raw else _today()
    ws, days = week_of(today)
    remaining = [d for d in days if d >= today]
    if not remaining:
        raise HTTPException(status_code=422, detail=MSG_NO_REMAINING_DAYS)

    overdue = (
        db.execute(
            select(PlanTask)
            .where(
                PlanTask.student_id == student.id,
                PlanTask.week_start == ws,
                PlanTask.date < today,
                PlanTask.status == "pending",
            )
            .order_by(PlanTask.order_index)
        )
        .scalars()
        .all()
    )
    if not overdue:
        return {"moved": 0, "days": {_iso(d): 0 for d in remaining}, "cap_per_day": 0, "week_start": _iso(ws)}

    weak_topics = set(
        db.execute(
            select(LearningState.topic_id).where(
                LearningState.student_id == student.id, LearningState.weakness.is_(True)
            )
        ).scalars().all()
    )
    payload = [
        {
            "id": t.id,
            "critical": t.kind == "review"
            or t.reason_code in ("review_critical", "weakness")
            or (t.topic_id in weak_topics if t.topic_id else False),
        }
        for t in overdue
    ]
    spread = domain.spread_recovery(payload, [d.isoformat() for d in remaining])

    by_id = {t.id: t for t in overdue}
    now = _utcnow()
    for d_iso, tlist in spread.items():
        d = dt.date.fromisoformat(d_iso)
        for i, entry in enumerate(tlist):
            t = by_id[entry["id"]]
            t.date = d
            t.source = "recovered"  # برچسب جبرانی برای UI (locked دست‌نخورده)
            if not t.reason_code:
                t.reason_code = "recovery"
            t.order_index = i + 1
            t.updated_at = now
    db.flush()

    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "recovered": len(overdue), "week_start": _iso(ws)}))
    return {
        "moved": len(overdue),
        "days": {d_iso: len(v) for d_iso, v in spread.items()},
        "cap_per_day": max(len(v) for v in spread.values()),
        "week_start": _iso(ws),
        "tomorrow_share": len(spread[remaining[0].isoformat()]),
    }


# --- priority / recommendation (doc 11.6، doc 08 §8.10) -------------------------------------------

def get_priority_week(db, student: Student) -> dict:
    ws, days = week_of(_today())
    snap = db.execute(
        select(PrioritySnapshot).where(PrioritySnapshot.student_id == student.id, PrioritySnapshot.week_start == ws)
    ).scalar_one_or_none()
    if snap is not None:
        items = snap.items
        generated = True
    else:
        taught_ids = set(
            db.execute(
                select(TaughtTopic.topic_id).where(
                    TaughtTopic.student_id == student.id, TaughtTopic.taught.is_(True)
                )
            ).scalars().all()
        )
        items = _priority_items(db, student, days, taught_ids)
        generated = False
    return {
        "week_start": _iso(ws),
        "week_start_jalali": _jalali_str(ws),
        "items": items,
        "from_snapshot": generated,
        "message": None if generated else "برای ذخیره snapshot، هفته را تولید کن.",
    }


def _rec_out(r: Recommendation) -> dict:
    return {
        "id": r.id,
        "date": _iso(r.date),
        "date_jalali": _jalali_str(r.date),
        "status": r.status,
        "payload": r.payload,
        "reasons": r.reasons,
    }


def recommendation_today(db, student: Student, create: bool = True) -> dict | None:
    today = _today()
    row = db.execute(
        select(Recommendation)
        .where(Recommendation.student_id == student.id, Recommendation.date == today)
        .order_by(Recommendation.created_at.desc())
    ).scalars().first()
    if row is not None or not create:
        return _rec_out(row) if row else None

    plan_items = [_task_out(t) for t in _day_tasks(db, student.id, today)]
    from app.modules.review import service as review_service

    q = review_service.queue(db, student)
    review_top = q["items"][:5]
    priority = get_priority_week(db, student)["items"]

    # doc 13.5 — procrastination aid به‌عنوان منبع پیشنهاد (models-only import، بدون چرخه)
    from app.modules.rewards import service as rewards_service

    aid = rewards_service.procrastination_for(db, student)
    picked = domain.recommendation_pick(plan_items, review_top, priority, procrastination=aid)
    row = Recommendation(
        student_id=student.id,
        date=today,
        payload=picked["payload"],
        reasons=[{"code": c, "fa": domain.reason_fa(c)} for c in picked["reasons"]],
        status="suggested",
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(row)
    db.flush()
    return _rec_out(row)


def recommendation_respond(db, student: Student, rec_id: str, status: str, payload: dict | None = None) -> dict:
    if status not in ("accepted", "rejected", "edited"):
        raise HTTPException(status_code=422, detail="وضعیت پاسخ باید accepted یا rejected یا edited باشد.")
    row = db.execute(
        select(Recommendation).where(Recommendation.id == rec_id, Recommendation.student_id == student.id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=MSG_REC_NOT_FOUND)
    if status == "edited":
        if payload:
            row.payload = payload
    row.status = status
    row.updated_at = _utcnow()
    db.flush()
    return _rec_out(row)


# --- today hub (doc 11.1 + doc 07.6) --------------------------------------------------------------

def _greeting() -> str:
    tehran_now = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=3, minutes=30)
    h = tehran_now.hour
    if 5 <= h < 12:
        return "صبح بخیر"
    if 12 <= h < 17:
        return "ظهر بخیر"
    if 17 <= h < 21:
        return "عصر بخیر"
    return "شب بخیر"


def today_out(db, student: Student) -> dict:
    today = _today()
    ws, days = week_of(today)

    # check-in امروز (بخش ۱)
    state: StateOut = student_get_state(db, student)

    # ظرفیت امروز (بخش ۲)
    cap = _capacity(db, student, today, force=False)

    # کارهای امروز (بخش ۳)
    plan_items = [_task_out(t) for t in _day_tasks(db, student.id, today)]

    # صف مرور ضروری (بخش ۴)
    from app.modules.review import service as review_service

    q = review_service.queue(db, student)
    review_top = q["items"][:5]

    # آزمون نزدیک (بخش ۵ — doc 07.6، فاز ۶ واقعی)
    exam_rows = db.execute(
        select(Exam)
        .where(
            Exam.student_id == student.id,
            Exam.status.in_(["planned", "in_progress"]),
            Exam.scheduled_date.is_not(None),
            Exam.scheduled_date >= today,
            Exam.scheduled_date <= today + dt.timedelta(days=7),
        )
        .order_by(Exam.scheduled_date)
    ).scalars().all()
    upcoming_exams: list = [
        {
            "id": e.id,
            "title": e.title,
            "kind": e.kind,
            "kind_fa": exam_domain.KIND_LABELS_FA.get(e.kind, e.kind),
            "status": e.status,
            "status_fa": exam_domain.STATUS_LABELS_FA.get(e.status, e.status),
            "scheduled_date": _iso(e.scheduled_date),
            "scheduled_date_jalali": _jalali_str(e.scheduled_date),
            "days_until": (e.scheduled_date - today).days,
            "subjects": list(e.subjects or []),
        }
        for e in exam_rows
    ]

    # پیشنهاد روز (بخش ۶)
    rec = recommendation_today(db, student, create=True)

    # sparkline هفت روز (بخش ۷)
    spark: list[dict] = []
    for i in range(6, -1, -1):
        d = today - dt.timedelta(days=i)
        day_tasks = _day_tasks(db, student.id, d)
        done_tasks = [t for t in day_tasks if t.status == "done"]
        attempts = int(
            db.execute(
                select(func.count()).select_from(AttemptResult).where(
                    AttemptResult.student_id == student.id,
                    func.date(AttemptResult.solved_at) == d.isoformat(),
                )
            ).scalar_one()
        )
        spark.append(
            {
                "date": _iso(d),
                "date_jalali": _jalali_str(d),
                "weekday_fa": WEEKDAYS_FA[_weekday(d)],
                "done_minutes": sum(t.minutes for t in done_tasks),
                "done_tasks": len(done_tasks),
                "planned_tasks": len(day_tasks),
                "attempts": attempts,
                "is_today": d == today,
            }
        )

    week_days_out = []
    for d in days:
        day_tasks = _day_tasks(db, student.id, d)
        week_days_out.append(
            {
                "date": _iso(d),
                "date_jalali": _jalali_str(d),
                "weekday_fa": WEEKDAYS_FA[_weekday(d)],
                "is_today": d == today,
                "tasks_count": len(day_tasks),
                "done_count": sum(1 for t in day_tasks if t.status == "done"),
                "locked_count": sum(1 for t in day_tasks if t.locked),
            }
        )

    return {
        "date": _iso(today),
        "date_jalali": _jalali_str(today),
        "weekday_fa": WEEKDAYS_FA[_weekday(today)],
        "greeting": _greeting(),
        "checkin": state.model_dump(mode="json"),
        "capacity": cap,
        "plan_items": plan_items,
        "plan_counts": {
            "total": len(plan_items),
            "done": sum(1 for t in plan_items if t["status"] == "done"),
            "locked": sum(1 for t in plan_items if t["locked"]),
        },
        "review_top": review_top,
        "review_due_count": q["due_count"],
        "upcoming_exams": upcoming_exams,
        "recommendation": rec,
        "week_sparkline": spark,
        "week": {"week_start": _iso(ws), "week_start_jalali": _jalali_str(ws), "days": week_days_out},
    }


# --- goals (doc 06 GET/POST /goals) ---------------------------------------------------------------

def _goal_out(g: Goal) -> dict:
    return {
        "id": g.id,
        "title": g.title,
        "kind": g.kind,
        "target_date": _iso(g.target_date),
        "target_date_jalali": _jalali_str(g.target_date),
        "created_at": g.created_at.isoformat() if g.created_at else None,
    }


def list_goals(db, student: Student, kind: str | None = None) -> list[dict]:
    q = select(Goal).where(Goal.student_id == student.id)
    if kind:
        q = q.where(Goal.kind == kind)
    rows = db.execute(q.order_by(Goal.created_at.desc())).scalars().all()
    return [_goal_out(g) for g in rows]


def create_goal(db, student: Student, title: str, kind: str, target_date: str | None) -> dict:
    title = (title or "").strip()
    if not title:
        raise HTTPException(status_code=422, detail=MSG_GOAL_TITLE)
    if kind not in ("long", "month", "week"):
        raise HTTPException(status_code=422, detail="نوع هدف باید long یا month یا week باشد.")
    g = Goal(
        student_id=student.id,
        title=title[:200],
        kind=kind,
        target_date=parse_date(target_date) if target_date else None,
        created_at=_utcnow(),
    )
    db.add(g)
    db.flush()
    return _goal_out(g)


def delete_goal(db, student: Student, goal_id: str) -> None:
    g = db.execute(select(Goal).where(Goal.id == goal_id, Goal.student_id == student.id)).scalar_one_or_none()
    if g is None:
        raise HTTPException(status_code=404, detail="هدف پیدا نشد.")
    db.delete(g)
    db.flush()
