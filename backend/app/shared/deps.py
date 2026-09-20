"""Shared FastAPI dependencies — auth (phase 1)."""
from __future__ import annotations

from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.student.models import Student

_bearer = HTTPBearer(auto_error=False)

MSG_UNAUTH = "برای ادامه باید وارد شوید."


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db=Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=401, detail=MSG_UNAUTH)
    try:
        payload = decode_access_token(creds.credentials)
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده است؛ دوباره وارد شوید.")
    user = db.execute(select(User).where(User.id == payload.get("sub"))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail=MSG_UNAUTH)
    return user


def get_current_student(
    user: User = Depends(get_current_user),
    db=Depends(get_db),
) -> Student:
    student = db.execute(select(Student).where(Student.user_id == user.id)).scalar_one_or_none()
    if student is None:
        # profile row is created at registration; if missing, repair it
        student = Student(user_id=user.id)
        db.add(student)
        db.flush()
    return student
