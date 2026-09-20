"""Planning & Capacity & Today Hub — FastAPI router (doc 06 §Planning).

مسیرها:
- GET/POST /goals · DELETE /goals/{id}
- GET/PUT /time-blocks
- GET /capacity?date=
- POST /school-override
- GET/PUT /plans/{date}
- POST /plans/generate-week · POST /plans/recover
- POST /plans/{date}/move-task · POST /plans/tasks/merge
- POST /plans/tasks/{id}/split · POST /plans/tasks/{id}/status · POST /plans/tasks/{id}/lock
- GET /today
- GET /recommendations/today · POST /recommendations/{id}/respond
- GET /priority/week

ترتیب ثبت: مسیرهای ثابت (generate-week/recover/tasks) قبل از /plans/{date}.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.events import PLAN_UPDATED, Event, event_bus

from app.db.session import get_db
from app.modules.planning import service
from app.modules.planning.schemas import (
    GenerateWeekIn,
    GoalIn,
    MergeTasksIn,
    MoveTaskIn,
    PlansPut,
    RecommendationRespondIn,
    RecoverIn,
    SchoolOverrideIn,
    SplitTaskIn,
    TaskLockIn,
    TaskStatusIn,
    TimeBlocksPut,
)
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["planning"])


# --- goals -------------------------------------------------------------------------

@router.get("/goals")
def list_goals(
    kind: str | None = Query(default=None),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    return ok(data={"items": service.list_goals(db, student, kind)})


@router.post("/goals")
def create_goal(
    body: GoalIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    goal = service.create_goal(db, student, body.title, body.kind, body.target_date)
    db.commit()
    return ok(data=goal)


@router.delete("/goals/{goal_id}")
def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    service.delete_goal(db, student, goal_id)
    db.commit()
    return ok(data={"deleted": goal_id})


# --- time blocks & capacity & school override ---------------------------------------

@router.get("/time-blocks")
def get_time_blocks(
    date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(date) if date else service._today()
    return ok(
        data={
            "date": service._iso(d),
            "date_jalali": service._jalali_str(d),
            "blocks": service.list_blocks(db, student, d),
        }
    )


@router.put("/time-blocks")
def put_time_blocks(
    body: TimeBlocksPut,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(body.date)
    result = service.put_blocks(db, student, d, body.blocks)
    db.commit()
    return ok(data=result)


@router.get("/capacity")
def get_capacity(
    date: str | None = Query(default=None),
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(date) if date else service._today()
    cap = service.get_capacity(db, student, d)
    db.commit()
    return ok(data=cap)


@router.post("/school-override")
def school_override(
    body: SchoolOverrideIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(body.date)
    result = service.school_override(db, student, d, body.school_off, body.blocks)
    db.commit()
    return ok(data=result)


# --- plans: ثابت‌ها قبل از {date} ------------------------------------------------------

@router.post("/plans/generate-week")
def generate_week(
    body: GenerateWeekIn | None = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.generate_week(db, student, body.week_start if body else None)
    db.commit()
    return ok(data=result)


@router.post("/plans/recover")
def recover_week(
    body: RecoverIn | None = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.recover_week(db, student, body.date if body else None)
    db.commit()
    return ok(data=result)


@router.post("/plans/tasks/merge")
def merge_tasks(
    body: MergeTasksIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.merge_tasks(db, student, body.task_ids)
    db.commit()
    return ok(data=result)


@router.post("/plans/tasks/{task_id}/split")
def split_task(
    task_id: str,
    body: SplitTaskIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.split_task(db, student, task_id, body.parts)
    db.commit()
    return ok(data=result)


@router.post("/plans/tasks/{task_id}/status")
def set_task_status(
    task_id: str,
    body: TaskStatusIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.set_task_status(db, student, task_id, body.status)
    db.commit()
    # بعد از commit — مصرف‌کننده (rewards ledger، فاز ۷): تکمیل کار = رویداد امتیازآور
    event_bus.publish(Event(PLAN_UPDATED, {"student_id": student.id, "task_id": task_id, "status": body.status}))
    return ok(data=result)


@router.post("/plans/tasks/{task_id}/lock")
def set_task_lock(
    task_id: str,
    body: TaskLockIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.set_task_lock(db, student, task_id, body.locked)
    db.commit()
    return ok(data=result)


@router.post("/plans/{date}/move-task")
def move_task(
    date: str,
    body: MoveTaskIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    to_date = service.parse_date(body.to_date)
    result = service.move_task(db, student, body.task_id, to_date)
    db.commit()
    return ok(data=result)


@router.get("/plans/{date}")
def get_plan(
    date: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(date)
    return ok(data=service.get_plan(db, student, d))


@router.put("/plans/{date}")
def put_plan(
    date: str,
    body: PlansPut,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    d = service.parse_date(date)
    result = service.put_plan(db, student, d, body.tasks)
    db.commit()
    return ok(data=result)


# --- today hub -------------------------------------------------------------------------

@router.get("/today")
def today(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    result = service.today_out(db, student)
    db.commit()  # recommendation on-demand ساخته می‌شود
    return ok(data=result)


# --- recommendations & priority ----------------------------------------------------------

@router.get("/recommendations/today")
def recommendation_today(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    rec = service.recommendation_today(db, student, create=True)
    db.commit()
    return ok(data=rec)


@router.post("/recommendations/{rec_id}/respond")
def recommendation_respond(
    rec_id: str,
    body: RecommendationRespondIn,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    result = service.recommendation_respond(db, student, rec_id, body.status, body.payload)
    db.commit()
    return ok(data=result)


@router.get("/priority/week")
def priority_week(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data=service.get_priority_week(db, student))
