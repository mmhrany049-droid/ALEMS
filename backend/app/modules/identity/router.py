"""User Identity — FastAPI router (doc 06 §Auth: /auth/*).

Envelope (doc 06) via app.shared.envelope.ok — error messages are Persian
(409 duplicate email, 401 bad credentials, 401 unauthorized).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity import service
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    AuthResponse,
    LoginRequest,
    MeResponse,
    RegisterRequest,
    UserOut,
)
from app.shared.deps import get_current_user
from app.shared.envelope import ok

router = APIRouter(tags=["identity"])


def _auth_data(user: User, db: Session) -> dict:
    token, ttl = service.issue_token(user)
    return AuthResponse(
        access_token=token,
        expires_in=ttl,
        user=UserOut.model_validate(user),
        student=service.student_profile(db, user),
    ).model_dump(mode="json")


@router.post("/auth/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    user, _student = service.register(db, body.email, body.password, body.full_name)
    db.commit()
    return ok(data=_auth_data(user, db))


@router.post("/auth/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = service.login(db, body.email, body.password)
    return ok(data=_auth_data(user, db))


@router.post("/auth/logout")
def logout(user: User = Depends(get_current_user)):
    # JWT is stateless: the client drops the token (doc 06 has the endpoint)
    return ok(data={"logged_out": True})


@router.get("/auth/me")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ok(data=service.me(db, user).model_dump(mode="json"))
