"""سرویس برنامه‌ریزی — اهداف، بلوک‌های زمانی، برنامه روزانه/هفتگی."""
from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.jalali import format_jalali_long, week_start as iso_week_start
from app.modules.identity.models import User
from app.modules.planning.domain import (
    OccupiedBlock,
    PlanningPolicy,
    generate_week_plan,
    summarize_week_items,
    validate_time_range,
)
from app.modules.planning.models import GOAL_TYPES, Goal, Plan, TimeBlock
from app.modules.settings.service import get_planning_policy
from app.shared.exceptions import NotFoundError, ValidationError


# ---------- اهداف ----------

def list_goals(db: Session, student_id: uuid.UUID, type_: str | None = None,
               status: str | None = None) -> list[Goal]:
    stmt = select(Goal).where(Goal.student_id == student_id).order_by(Goal.start_date.desc())
    if type_:
        stmt = stmt.where(Goal.type == type_)
    if status:
        stmt = stmt.where(Goal.status == status)
    return list(db.scalars(stmt))


def get_goal(db: Session, student_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None or goal.student_id != student_id:
        raise NotFoundError("هدف مورد نظر یافت نشد.")
    return goal


def create_goal(db: Session, student_id: uuid.UUID, data: dict) -> Goal:
    goal = Goal(student_id=student_id, **data)
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def update_goal(db: Session, student_id: uuid.UUID, goal_id: uuid.UUID, data: dict) -> Goal:
    goal = get_goal(db, student_id, goal_id)
    for key, value in data.items():
        if value is not None:
            setattr(goal, key, value)
    if goal.end_date < goal.start_date:
        raise ValidationError("تاریخ پایان هدف نمی‌تواند قبل از تاریخ شروع باشد.")
    db.commit()
    db.refresh(goal)
    return goal


def delete_goal(db: Session, student_id: uuid.UUID, goal_id: uuid.UUID) -> None:
    goal = get_goal(db, student_id, goal_id)
    db.delete(goal)
    db.commit()


# ---------- بلوک‌های زمانی ----------

def list_time_blocks(db: Session, student_id: uuid.UUID) -> list[TimeBlock]:
    return list(db.scalars(
        select(TimeBlock).where(TimeBlock.student_id == student_id)
        .order_by(TimeBlock.day_of_week, TimeBlock.start_time)
    ))


def replace_time_blocks(db: Session, student_id: uuid.UUID, blocks: list[dict]) -> list[TimeBlock]:
    """جایگزینی کامل بلوک‌های هفتگی."""
    parsed: list[dict] = []
    for block in blocks:
        start_t, end_t = validate_time_range(block["start_time"], block["end_time"])
        parsed.append({**block, "start_time": start_t, "end_time": end_t})
    db.query(TimeBlock).filter(TimeBlock.student_id == student_id).delete()
    rows = [TimeBlock(student_id=student_id, **block) for block in parsed]
    db.add_all(rows)
    db.commit()
    return list_time_blocks(db, student_id)


# ---------- برنامه‌ها ----------

def get_plan(db: Session, student_id: uuid.UUID, day: date) -> Plan | None:
    return db.scalar(select(Plan).where(Plan.student_id == student_id, Plan.date == day))


def upsert_plan(db: Session, student_id: uuid.UUID, day: date,
                items: list[dict], status: str | None = None) -> Plan:
    """ایجاد/ویرایش برنامه روز (AT-18)."""
    plan = get_plan(db, student_id, day)
    if plan is None:
        plan = Plan(student_id=student_id, date=day, items=items,
                    status=status or "active")
        db.add(plan)
    else:
        plan.items = items
        if status:
            plan.status = status
    db.commit()
    db.refresh(plan)
    return plan


def generate_week(db: Session, user: User, week_start: date,
                  goal_ids: list[uuid.UUID] | None = None) -> dict:
    """تولید برنامه هفتگی بر اساس بلوک‌های اشغال و اهداف هفتگی (AT-17).

    خروجی: برنامه‌های ۷ روز ذخیره‌شده + خلاصه.
    """
    expected_start = iso_week_start(week_start)
    if week_start != expected_start:
        raise ValidationError(
            f"تاریخ شروع هفته باید شنبه باشد. شنبه این هفته: {expected_start.isoformat()}"
        )

    policy = get_planning_policy(db)

    blocks = list_time_blocks(db, user.id)
    occupied_by_day: dict[int, list[OccupiedBlock]] = {}
    for day in range(7):
        occupied_by_day[day] = [
            OccupiedBlock(start=b.start_time, end=b.end_time, title=b.title)
            for b in blocks if b.day_of_week == day and b.block_type in ("school", "class")
        ]

    goals = [
        g for g in list_goals(db, user.id, type_="weekly", status="active")
        if not goal_ids or g.id in goal_ids
    ]
    days = [week_start + timedelta(days=i) for i in range(7)]
    # توزیع اهداف بین روزها (هر هدف بین روزهای باقی هفته پخش می‌شود)
    goal_inputs: list[dict] = []
    for goal in goals:
        span = max(1, (min(goal.end_date, days[-1]) - max(goal.start_date, days[0])).days + 1)
        target_minutes = _goal_minutes(goal)
        per_day = max(1, target_minutes // max(1, min(span, 7)))
        goal_inputs.append({
            "title": goal.title, "subject": (goal.target_value or {}).get("subject"),
            "minutes": per_day, "goal_id": str(goal.id),
        })

    week_plan = generate_week_plan(week_start=week_start, occupied_by_day=occupied_by_day,
                                   goals=goal_inputs, policy=policy)

    saved: list[Plan] = []
    for day_index, day in enumerate(days):
        plan = upsert_plan(db, user.id, day, week_plan.get(day_index, []), status="active")
        saved.append(plan)

    return {
        "week_start": week_start.isoformat(),
        "week_start_label": format_jalali_long(week_start),
        "plans": [plan_payload(p) for p in saved],
        "summary": {str(d): summarize_week_items(p.items) for d, p in zip(days, saved)},
    }


def _goal_minutes(goal: Goal) -> int:
    value = goal.target_value or {}
    minutes = value.get("minutes")
    if isinstance(minutes, (int, float)) and minutes > 0:
        return int(minutes)
    hours = value.get("hours")
    if isinstance(hours, (int, float)) and hours > 0:
        return int(hours * 60)
    return 90  # پیش‌فرض معقول: ۹۰ دقیقه در روز برای این هدف


# ---------- پیلودها ----------

def goal_payload(goal: Goal) -> dict:
    return {
        "id": str(goal.id),
        "type": goal.type,
        "title": goal.title,
        "target_value": goal.target_value or {},
        "start_date": goal.start_date.isoformat(),
        "end_date": goal.end_date.isoformat(),
        "status": goal.status,
        "type_label": {"long": "بلندمدت", "monthly": "ماهانه", "weekly": "هفتگی"}[goal.type],
    }


def time_block_payload(block: TimeBlock) -> dict:
    return {
        "id": str(block.id),
        "day_of_week": block.day_of_week,
        "start_time": block.start_time.isoformat(timespec="minutes"),
        "end_time": block.end_time.isoformat(timespec="minutes"),
        "block_type": block.block_type,
        "title": block.title,
    }


def plan_payload(plan: Plan) -> dict:
    return {
        "id": str(plan.id),
        "date": plan.date.isoformat(),
        "items": plan.items or [],
        "status": plan.status,
        "summary": summarize_week_items(plan.items or []),
    }
