"""روتر ماژول برنامه‌ریزی — /api/v1/goals، /time-blocks، /plans"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.identity.service import current_user
from app.modules.planning.schemas import GoalIn, GoalUpdateIn, GenerateWeekIn, PlanIn, TimeBlocksIn
from app.modules.planning.service import (
    create_goal,
    delete_goal,
    generate_week,
    get_plan,
    goal_payload,
    list_goals,
    list_time_blocks,
    plan_payload,
    replace_time_blocks,
    time_block_payload,
    update_goal,
    upsert_plan,
)
from app.shared.response import ok

router = APIRouter(tags=["planning"])


# ---------- اهداف ----------

@router.get("/goals", response_model=dict)
def get_goals(
    type: str | None = Query(None),
    status: str | None = Query(None),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    goals = list_goals(db, user.id, type_=type, status=status)
    return ok([goal_payload(g) for g in goals])


@router.post("/goals", response_model=dict)
def post_goal(
    payload: GoalIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """تعریف هدف (AT-15)."""
    return ok(goal_payload(create_goal(db, user.id, payload.model_dump())))


@router.put("/goals/{goal_id}", response_model=dict)
def put_goal(
    goal_id: uuid.UUID,
    payload: GoalUpdateIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok(goal_payload(update_goal(db, user.id, goal_id,
                                       payload.model_dump(exclude_unset=True))))


@router.delete("/goals/{goal_id}", response_model=dict)
def delete_goal_endpoint(
    goal_id: uuid.UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    delete_goal(db, user.id, goal_id)
    return ok({"detail": "هدف حذف شد."})


# ---------- بلوک‌های زمانی ----------

@router.get("/time-blocks", response_model=dict)
def get_time_blocks(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    return ok([time_block_payload(b) for b in list_time_blocks(db, user.id)])


@router.put("/time-blocks", response_model=dict)
def put_time_blocks(
    payload: TimeBlocksIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ثبت بلوک‌های زمانی ثابت هفتگی (AT-16)."""
    blocks = replace_time_blocks(db, user.id, [b.model_dump() for b in payload.blocks])
    return ok([time_block_payload(b) for b in blocks])


# ---------- برنامه‌ها ----------

@router.get("/plans", response_model=dict)
def get_plans(
    date: date = Query(..., alias="date", description="تاریخ برنامه"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    plan = get_plan(db, user.id, date)
    return ok(plan_payload(plan) if plan else None)


@router.put("/plans/{plan_date}", response_model=dict)
def put_plan(
    plan_date: date,
    payload: PlanIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """ویرایش برنامه روز (AT-18)."""
    plan = upsert_plan(db, user.id, plan_date, [i.model_dump() for i in payload.items],
                       status=payload.status)
    return ok(plan_payload(plan))


@router.post("/plans/generate-week", response_model=dict)
def post_generate_week(
    payload: GenerateWeekIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict:
    """تولید برنامه هفتگی (AT-17)."""
    return ok(generate_week(db, user, payload.week_start, payload.goal_ids))
