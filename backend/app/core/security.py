"""امنیت — هش رمز عبور (bcrypt) و توکن JWT (Session Management Module)."""
from __future__ import annotations

import datetime as dt
import uuid

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """هش امن رمز عبور با bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """بررسی صحت رمز عبور."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    """ساخت توکن JWT برای نشست کاربر (با شناسه یکتای نشست برای امکان خروج)."""
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """اعتبارسنجی توکن؛ در صورت نامعتبر بودن None برمی‌گرداند."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError:
        return None
