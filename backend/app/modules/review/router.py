"""Review & Learning — FastAPI router (doc 06 §Review).

مسیرها:
- GET  /reviews/queue
- POST /reviews/{review_id}/complete
- POST /reviews/{review_id}/postpone
- POST /reviews/rebuild
- GET  /reviews/cluster-suggestion
- GET  /reviews/learning-states   (doc 10 §10.4)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.review import service
from app.modules.review.schemas import PostponeIn
from app.modules.student.models import Student
from app.shared.deps import get_current_student
from app.shared.envelope import ok

router = APIRouter(tags=["review"])


@router.get("/reviews/queue")
def get_queue(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data=service.queue(db, student))


@router.post("/reviews/rebuild")
def rebuild(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    result = service.rebuild(db, student)
    db.commit()
    return ok(data=result)


@router.get("/reviews/cluster-suggestion")
def cluster_suggestion(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data=service.cluster_suggestion(db, student))


@router.get("/reviews/learning-states")
def get_learning_states(db: Session = Depends(get_db), student: Student = Depends(get_current_student)):
    return ok(data={"items": service.learning_states(db, student)})


@router.post("/reviews/{review_id}/complete")
def complete(
    review_id: str,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    item = service.complete(db, student, review_id)
    db.commit()
    return ok(data=item)


@router.post("/reviews/{review_id}/postpone")
def postpone(
    review_id: str,
    body: PostponeIn | None = None,
    db: Session = Depends(get_db),
    student: Student = Depends(get_current_student),
):
    item = service.postpone(db, student, review_id, (body or PostponeIn()).days)
    db.commit()
    return ok(data=item)
