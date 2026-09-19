"""سرویس هویت — ساخت کاربر، ورود، خروج و وابستگی‌های احراز هویت."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.db.session import get_db
from app.modules.identity.models import ROLES, SessionToken, User
from app.modules.identity.schemas import LoginIn, RegisterIn, TokenOut, UserOut
from app.shared.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError, ValidationError


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def create_user(db: Session, payload: RegisterIn) -> User:
    from app.modules.identity.domain import validate_password, validate_username

    username = validate_username(payload.username)
    validate_password(payload.password)
    if get_user_by_username(db, username) is not None:
        raise ConflictError("این نام کاربری قبلاً ثبت شده است. نام دیگری انتخاب کنید.")
    user = User(username=username, password_hash=hash_password(payload.password), role="student")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, payload: LoginIn) -> TokenOut:
    """ورود کاربر — خطاهای واضح فارسی برمی‌گرداند (AT-03)."""
    user = get_user_by_username(db, payload.username.strip())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("نام کاربری یا رمز عبور اشتباه است.")
    user.last_login_at = datetime.utcnow()
    token = create_access_token(user.id, user.role)
    jti = _extract_jti(token)
    db.add(SessionToken(
        user_id=user.id,
        token_jti=jti,
        expires_at=datetime.utcnow() + _token_ttl(),
    ))
    db.commit()
    db.refresh(user)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


def logout(db: Session, token: str) -> None:
    """لغو نشست جاری."""
    payload = decode_access_token(token)
    if not payload:
        return
    jti = payload.get("jti")
    if not jti:
        return
    session_row = db.scalar(select(SessionToken).where(SessionToken.token_jti == jti))
    if session_row and session_row.revoked_at is None:
        session_row.revoked_at = datetime.utcnow()
        db.commit()


def _extract_jti(token: str) -> str:
    import jwt as pyjwt

    payload = pyjwt.decode(token, options={"verify_signature": False})
    return payload.get("jti", "")


def _token_ttl():
    from datetime import timedelta

    from app.core.config import settings

    return timedelta(minutes=settings.access_token_expire_minutes)


# ---------- وابستگی‌های FastAPI ----------

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402

_bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """کاربر جاری از روی توکن Bearer."""
    if credentials is None:
        raise UnauthorizedError("برای دسترسی ابتدا وارد شوید.")
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise UnauthorizedError("نشست شما منقضی یا نامعتبر است. دوباره وارد شوید.")
    jti = payload.get("jti")
    if jti:
        row = db.scalar(select(SessionToken).where(SessionToken.token_jti == jti))
        if row is not None and row.revoked_at is not None:
            raise UnauthorizedError("این نشست خاتمه یافته است. دوباره وارد شوید.")
    user = db.get(User, uuid.UUID(payload["sub"]))
    if user is None:
        raise NotFoundError("کاربر یافت نشد.")
    return user


def require_admin(user: User = Depends(current_user)) -> User:
    """دسترسی فقط برای مدیر."""
    if user.role not in ROLES or user.role != "admin":
        raise ForbiddenError("این عملیات فقط برای مدیر سیستم مجاز است.")
    return user
