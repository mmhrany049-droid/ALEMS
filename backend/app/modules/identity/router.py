"""روتر ماژول هویت — /api/v1/auth"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.identity.models import User
from app.modules.identity.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.modules.identity.service import authenticate, create_user, current_user, logout
from app.shared.response import ok

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)


@router.post("/register", response_model=dict)
def register(payload: RegisterIn, db: Session = Depends(get_db)) -> dict:
    """ثبت کاربر جدید."""
    user = create_user(db, payload)
    return ok(UserOut.model_validate(user).model_dump(mode="json"))


@router.post("/login", response_model=dict)
def login(payload: LoginIn, db: Session = Depends(get_db)) -> dict:
    """ورود و دریافت توکن/نشست."""
    token = authenticate(db, payload)
    return ok(token.model_dump(mode="json"))


@router.post("/logout", response_model=dict)
def do_logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> dict:
    """خروج و لغو نشست جاری."""
    if credentials is not None:
        logout(db, credentials.credentials)
    return ok({"detail": "با موفقیت خارج شدید."})


@router.get("/me", response_model=dict)
def me(user: User = Depends(current_user)) -> dict:
    """اطلاعات کاربر جاری."""
    return ok(UserOut.model_validate(user).model_dump(mode="json"))
