"""User Identity — pure domain rules, NO I/O (doc 03 §3.1)."""
from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_valid_email(email: str) -> bool:
    return bool(_EMAIL_RE.match(email or ""))


def is_valid_password(password: str) -> bool:
    """Minimum policy: 8..128 chars (bcrypt input limit)."""
    return bool(password) and 8 <= len(password) <= 128


ROLES = ("student", "advisor", "parent", "admin")  # doc 04 Permission


def normalize_role(role: str | None) -> str:
    return role if role in ROLES else "student"
