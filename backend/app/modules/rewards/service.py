"""Motivation (Rewards & Behavior) — application services / use-cases (doc 03 §3.1، doc 13).

رویدادهای دامنه از app.core.events emit می‌شوند (doc 03 §3.4 — rewards مصرف‌کننده است):
  PLAN_UPDATED(status=done) · REVIEW_COMPLETED · TEST_RECORDS_CREATED(finished) · CHECKIN_SUBMITTED
ledger append-only + امضای یکتایی (student, source, ref) → رویداد تکراری امتیاز دوباره نمی‌گیرد.
"""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.events import (
    CHECKIN_SUBMITTED,
    PLAN_UPDATED,
    REVIEW_COMPLETED,
    TEST_RECORDS_CREATED,
    Event,
    event_bus,
)
from app.core.jalali import gregorian_to_jalali, jalali_to_gregorian
from app.db.session import session_scope
from app.modules.academic.models import Topic
from app.modules.activity.models import AttemptResult
from app.modules.exam.models import Exam
from app.modules.planning.models import PlanTask
from app.modules.rewards import domain
from app.modules.rewards.models import Badge, BadgeAward, PointsEntry, StreakState
from app.modules.review.models import LearningState
from app.modules.settings.service import get_all as get_settings_map
from app.modules.student.models import Checkin, Student

logger = logging.getLogger("alems.rewards")

TZ_TEHRAN = dt.timezone(dt.timedelta(hours=3, minutes=30))


# --- تاریخ ----------------------------------------------------------------------------------

def _today() -> dt.date:
    return dt.datetime.now(dt.timezone.utc).astimezone(TZ_TEHRAN).date()


def _jalali_iso(d: dt.date) -> str:
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{jy:04d}/{jm:02d}/{jd:02d}"


def _from_jalali_iso(s: str) -> dt.date:
    parts = s.replace("-", "/").split("/")
    gy, gm, gd = jalali_to_gregorian(int(parts[0]), int(parts[1]), int(parts[2]))
    return dt.date(gy, gm, gd)


def _grace(db: Session) -> int:
    try:
        return int(get_settings_map(db).get("streak_grace_days", domain.STREAK_GRACE_DEFAULT))
    except (TypeError, ValueError):
        return domain.STREAK_GRACE_DEFAULT


# --- seed نشان‌ها (doc 13.3 — OD4: ۸ تا ۱۲) ----------------------------------------------------

def ensure_badge_seed(db: Session) -> None:
    """idempotent — badgeهای seed که نیستند ساخته می‌شوند."""
    existing = set(db.execute(select(Badge.code)).scalars().all())
    added = 0
    for b in domain.BADGE_SEED:
        if b["code"] in existing:
            continue
        db.add(Badge(code=b["code"], title_fa=b["title_fa"], description_fa=b["description_fa"],
                     kind=b["kind"], target=b["target"]))
        added += 1
    if added:
        db.flush()


# --- award (ledger append-only) ------------------------------------------------------------------

def _ledger_days(db: Session, student_id: str) -> set[dt.date]:
    rows = db.execute(
        select(PointsEntry.active_date).where(PointsEntry.student_id == student_id).distinct()
    ).scalars().all()
    out = set()
    for s in rows:
        try:
            out.add(_from_jalali_iso(s))
        except (ValueError, IndexError):  # pragma: no cover — داده خراب
            continue
    return out


def _upsert_streak(db: Session, student_id: str) -> StreakState:
    days = _ledger_days(db, student_id)
    current, longest = domain.streaks_from_days(days, _today(), _grace(db))
    row = db.execute(select(StreakState).where(StreakState.student_id == student_id)).scalar_one_or_none()
    last = _jalali_iso(max(days)) if days else None
    if row is None:
        row = StreakState(student_id=student_id, current_streak=current, longest_streak=longest,
                          last_active_date=last, updated_at=dt.datetime.now(dt.timezone.utc))
        db.add(row)
    else:
        row.current_streak = current
        row.longest_streak = longest
        row.last_active_date = last
        row.updated_at = dt.datetime.now(dt.timezone.utc)
    db.flush()
    return row


def _aggregates(db: Session, student_id: str, streak_longest: int) -> dict[str, int]:
    points_total = db.execute(
        select(func.coalesce(func.sum(PointsEntry.points), 0)).where(PointsEntry.student_id == student_id)
    ).scalar_one()
    active_days = db.execute(
        select(func.count(func.distinct(PointsEntry.active_date))).where(PointsEntry.student_id == student_id)
    ).scalar_one()
    reviews = db.execute(
        select(func.count(PointsEntry.id)).where(
            PointsEntry.student_id == student_id, PointsEntry.source_event == domain.SOURCE_REVIEW)
    ).scalar_one()
    sessions = db.execute(
        select(func.count(PointsEntry.id)).where(
            PointsEntry.student_id == student_id, PointsEntry.source_event == domain.SOURCE_SESSION)
    ).scalar_one()
    exams = db.execute(
        select(func.count(Exam.id)).where(Exam.student_id == student_id, Exam.status == "finished")
    ).scalar_one()
    answers = db.execute(
        select(func.count(AttemptResult.id)).where(
            AttemptResult.student_id == student_id, AttemptResult.status == "answered")
    ).scalar_one()
    return {
        "points": int(points_total),
        "active_days": int(active_days),
        "reviews": int(reviews),
        "sessions": int(sessions),
        "exams": int(exams),
        "answers": int(answers),
        "streak": int(streak_longest),
    }


def _evaluate_badges(db: Session, student_id: str, agg: dict[str, int]) -> list[dict[str, Any]]:
    ensure_badge_seed(db)
    awarded = {
        a.badge_id: a for a in db.execute(
            select(BadgeAward).where(BadgeAward.student_id == student_id)
        ).scalars().all()
    }
    new_awards = []
    for badge in db.execute(select(Badge)).scalars().all():
        if badge.id in awarded:
            continue
        value = agg.get(badge.kind, 0)
        if domain.badge_earned(badge.kind, value, badge.target):
            aw = BadgeAward(student_id=student_id, badge_id=badge.id,
                            evidence={"kind": badge.kind, "value": value, "target": badge.target})
            db.add(aw)
            new_awards.append({"code": badge.code, "title_fa": badge.title_fa})
    if new_awards:
        db.flush()
    return new_awards


def _award(student_id: str, source_event: str, ref_id: str, active_date: str | None = None) -> bool:
    """یک رویداد امتیازآور — idempotent (unique ledger). consumerها این را صدا می‌زنند."""
    points = domain.POINTS_BY_SOURCE.get(source_event)
    if points is None:  # pragma: no cover
        return False
    with session_scope() as db:
        exists = db.execute(
            select(PointsEntry.id).where(
                PointsEntry.student_id == student_id,
                PointsEntry.source_event == source_event,
                PointsEntry.ref_id == str(ref_id),
            )
        ).scalar_one_or_none()
        if exists is not None:
            return False
        try:
            db.add(PointsEntry(
                student_id=student_id, source_event=source_event, ref_id=str(ref_id),
                points=points, active_date=active_date or _jalali_iso(_today()),
            ))
            db.flush()
        except IntegrityError:  # race — امضای یکتا برنده است
            db.rollback()
            return False
        streak = _upsert_streak(db, student_id)
        agg = _aggregates(db, student_id, streak.longest_streak)
        new_badges = _evaluate_badges(db, student_id, agg)
        logger.info(
            "points awarded student=%s source=%s pts=%d total=%d streak=%d new_badges=%s",
            student_id, source_event, points, agg["points"], streak.current_streak,
            [b["code"] for b in new_badges],
        )
        return True


# --- مصرف‌کنندگان رویداد (doc 03 §3.4) -------------------------------------------------------------

def _on_plan_updated(event: Event) -> None:
    if event.payload.get("status") != "done":
        return
    task_id = event.payload.get("task_id")
    student_id = event.payload.get("student_id")
    if task_id and student_id:
        _award(student_id, domain.SOURCE_TASK, task_id)


def _on_review_completed(event: Event) -> None:
    student_id = event.payload.get("student_id")
    item_id = event.payload.get("item_id")
    if student_id and item_id:
        cycle = event.payload.get("cycle_index") or 0
        _award(student_id, domain.SOURCE_REVIEW, f"{item_id}:{cycle}")


def _on_test_records(event: Event) -> None:
    # فقط finish واقعی جلسه — نه هر records و نه past-import (فعالیت مطالعاتی معتبر، doc 08 §8.9)
    if not event.payload.get("finished"):
        return
    student_id = event.payload.get("student_id")
    session_id = event.payload.get("session_id")
    if student_id and session_id:
        _award(student_id, domain.SOURCE_SESSION, session_id)


def _on_checkin(event: Event) -> None:
    student_id = event.payload.get("student_id")
    day = event.payload.get("date")  # میلادی ISO از student service
    if student_id and day:
        try:
            g = dt.date.fromisoformat(str(day))
            active = _jalali_iso(g)
        except ValueError:
            active = None
        _award(student_id, domain.SOURCE_CHECKIN, str(day), active_date=active)


_consumers_registered = False


def register_event_consumers() -> None:
    global _consumers_registered
    if _consumers_registered:
        return
    event_bus.subscribe(PLAN_UPDATED, _on_plan_updated)
    event_bus.subscribe(REVIEW_COMPLETED, _on_review_completed)
    event_bus.subscribe(TEST_RECORDS_CREATED, _on_test_records)
    event_bus.subscribe(CHECKIN_SUBMITTED, _on_checkin)
    _consumers_registered = True


# --- 13.4 habit advice --------------------------------------------------------------------------

def habit_advice_out(db: Session, student_id: str) -> dict[str, Any]:
    data_days = db.execute(
        select(func.count(func.distinct(PointsEntry.active_date))).where(PointsEntry.student_id == student_id)
    ).scalar_one()
    rows = db.execute(
        select(PointsEntry.active_date, func.count(PointsEntry.id))
        .where(PointsEntry.student_id == student_id, PointsEntry.source_event == domain.SOURCE_TASK)
        .group_by(PointsEntry.active_date)
    ).all()
    advice = domain.habit_advice([int(c) for _d, c in rows], int(data_days))
    if advice is None:
        return {"available": False, "data_days": int(data_days), "min_data_days": domain.HABIT_MIN_DATA_DAYS}
    return {"available": True, **advice}


# --- 13.5 procrastination aid ---------------------------------------------------------------------

def procrastination_for(db: Session, student: Student) -> dict[str, Any] | None:
    today = _today()
    window = [today - dt.timedelta(days=i) for i in range(domain.PROCRAST_WINDOW_DAYS)]
    day_stats = []
    for d in window:
        total = db.execute(
            select(func.count(PlanTask.id)).where(PlanTask.student_id == student.id, PlanTask.date == d)
        ).scalar_one()
        done = db.execute(
            select(func.count(PlanTask.id)).where(
                PlanTask.student_id == student.id, PlanTask.date == d, PlanTask.status == "done")
        ).scalar_one()
        day_stats.append({"date": d.isoformat(), "done": int(done), "total": int(total)})
    big_rows = db.execute(
        select(PlanTask).where(
            PlanTask.student_id == student.id,
            PlanTask.status == "pending",
            PlanTask.date <= today,
            PlanTask.minutes >= domain.PROCRAST_BIG_TASK_MINUTES,
        ).order_by(PlanTask.date.asc())
    ).scalars().all()
    big_tasks = [{"id": t.id, "title": t.title, "minutes": t.minutes} for t in big_rows]

    weak_topic = None
    states = db.execute(
        select(LearningState).where(
            LearningState.student_id == student.id, LearningState.exam_readiness.is_not(None)
        )
    ).scalars().all()
    if states:
        weakest = min(states, key=lambda s: (s.exam_readiness if s.exam_readiness is not None else 1.0))
        if (weakest.exam_readiness or 0) < 0.6:
            title = db.execute(select(Topic.title).where(Topic.id == weakest.topic_id)).scalar_one_or_none()
            weak_topic = {"topic_id": weakest.topic_id, "topic_title": title}

    return domain.procrastination_aid(day_stats, big_tasks, weak_topic)


# --- خروجی‌ها (doc 06: GET /rewards/summary · GET /rewards/badges) ----------------------------------

def _latest_checkin(db: Session, student_id: str) -> dict[str, Any] | None:
    row = db.execute(
        select(Checkin).where(Checkin.student_id == student_id).order_by(Checkin.date.desc()).limit(1)
    ).scalar_one_or_none()
    if row is None:
        return None
    return {
        "date": row.date.isoformat(),
        "date_jalali": _jalali_iso(row.date),
        "energy": row.energy, "focus": row.focus, "motivation": row.motivation,
        "stress": row.stress, "fatigue": row.fatigue,
    }


def summary(db: Session, student: Student) -> dict[str, Any]:
    ensure_badge_seed(db)
    streak = _upsert_streak(db, student.id)  # همیشه تازه (روز عوض شده باشد → current=0)
    agg = _aggregates(db, student.id, streak.longest_streak)
    by_source = {
        src: db.execute(
            select(func.count(PointsEntry.id)).where(
                PointsEntry.student_id == student.id, PointsEntry.source_event == src)
        ).scalar_one()
        for src in domain.ALL_SOURCES
    }
    recent_awards = db.execute(
        select(BadgeAward).where(BadgeAward.student_id == student.id)
        .order_by(BadgeAward.awarded_at.desc()).limit(3)
    ).scalars().all()
    badges_by_id = {b.id: b for b in db.execute(select(Badge)).scalars().all()}
    earned_count = db.execute(
        select(func.count(BadgeAward.id)).where(BadgeAward.student_id == student.id)
    ).scalar_one()
    return {
        "points_total": agg["points"],
        "points_by_source": {domain.SOURCE_FA[s]: by_source[s] for s in domain.ALL_SOURCES},
        "streak": {
            "current": streak.current_streak,
            "longest": streak.longest_streak,
            "last_active_date": streak.last_active_date,
            "grace_days": _grace(db),
        },
        "badges": {
            "earned_count": int(earned_count),
            "total": len(badges_by_id),
            "recent": [
                {"code": badges_by_id[a.badge_id].code, "title_fa": badges_by_id[a.badge_id].title_fa}
                for a in recent_awards if a.badge_id in badges_by_id
            ],
        },
        "habit_advice": habit_advice_out(db, student.id),
        "procrastination": procrastination_for(db, student),
        "latest_checkin": _latest_checkin(db, student.id),
    }


def badges_out(db: Session, student: Student) -> dict[str, Any]:
    ensure_badge_seed(db)
    streak = _upsert_streak(db, student.id)
    agg = _aggregates(db, student.id, streak.longest_streak)
    # badgeهای تازه را هم ارزیابی کن (GET نباید از award عقب بماند)
    _evaluate_badges(db, student.id, agg)
    awarded = {
        a.badge_id: a for a in db.execute(
            select(BadgeAward).where(BadgeAward.student_id == student.id)
        ).scalars().all()
    }
    items = []
    for b in db.execute(select(Badge).order_by(Badge.target.asc())).scalars().all():
        aw = awarded.get(b.id)
        value = agg.get(b.kind, 0)
        items.append({
            "code": b.code,
            "title_fa": b.title_fa,
            "description_fa": b.description_fa,
            "kind": b.kind,
            "target": b.target,
            "earned": aw is not None,
            "awarded_at": aw.awarded_at.isoformat() if aw else None,
            "progress": {"value": min(value, b.target), "current": value, "target": b.target},
        })
    return {"items": items, "earned_count": len(awarded)}
