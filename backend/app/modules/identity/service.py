"""User Identity — application services (doc 06 §Auth).

register → User + Student profile row (doc 04 Student Profile)
login → JWT; logout → stateless success (client drops the token)
"""
from __future__ import annotations

from fastapi.exceptions import HTTPException
from sqlalchemy import select

from app.core.security import create_access_token, hash_password, verify_password
from app.modules.identity.models import User
from app.modules.identity.schemas import MeResponse, UserOut
from app.modules.student.models import Student
from app.modules.student.schemas import StudentProfileOut

MSG_EMAIL_EXISTS = "این ایمیل قبلاً ثبت شده است."
MSG_BAD_CREDENTIALS = "ایمیل یا رمز عبور نادرست است."


def register(db, email: str, password: str, full_name: str | None) -> tuple[User, Student]:
    email = email.lower().strip()
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail=MSG_EMAIL_EXISTS)
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role="student")
    db.add(user)
    db.flush()
    student = Student(user_id=user.id)
    db.add(student)
    db.flush()
    return user, student


def login(db, email: str, password: str) -> User:
    email = email.lower().strip()
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=401, detail=MSG_BAD_CREDENTIALS)
    return user


def issue_token(user: User) -> tuple[str, int]:
    return create_access_token(user.id, user.role)


def student_profile(db, user: User) -> StudentProfileOut | None:
    s = db.execute(select(Student).where(Student.user_id == user.id)).scalar_one_or_none()
    if s is None:
        return None
    return StudentProfileOut(id=s.id, user_id=s.user_id, grade=s.grade, track=s.track, target=s.target)


def me(db, user: User) -> MeResponse:
    return MeResponse(user=UserOut.model_validate(user), student=student_profile(db, user))
