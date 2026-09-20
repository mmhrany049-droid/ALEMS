"""Security — bcrypt password + JWT access tokens (doc 03 §3.6, phase 1).

- register/login (bcrypt)
- JWT HS256 access token, TTL from Settings (ACCESS_TOKEN_TTL_MINUTES)
No external data leaves the core (doc 03 §3.6).
"""
from __future__ import annotations

import datetime as dt

import bcrypt
import jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def create_access_token(user_id: str, role: str) -> tuple[str, int]:
    """Return (token, ttl_seconds)."""
    s = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + dt.timedelta(minutes=s.ACCESS_TOKEN_TTL_MINUTES),
    }
    return jwt.encode(payload, s.SECRET_KEY, algorithm=ALGORITHM), s.ACCESS_TOKEN_TTL_MINUTES * 60


class InvalidTokenError(ValueError):
    """Token missing/expired/malformed."""


def decode_access_token(token: str) -> dict:
    s = get_settings()
    try:
        return jwt.decode(token, s.SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError as e:
        raise InvalidTokenError(str(e)) from e
