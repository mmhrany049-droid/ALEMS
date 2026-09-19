"""منطق دامنه هویت — قوانین نام کاربری و رمز عبور (خالص و قابل‌تست)."""
from __future__ import annotations

import re

from app.shared.exceptions import ValidationError

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{3,64}$")


def validate_username(username: str) -> str:
    """اعتبارسنجی نام کاربری — حروف انگلیسی، عدد، نقطه، خط تیره و زیرخط."""
    username = username.strip()
    if not username:
        raise ValidationError("نام کاربری نمی‌تواند خالی باشد.")
    if not USERNAME_RE.match(username):
        raise ValidationError(
            "نام کاربری باید ۳ تا ۶۴ کاراکتر و شامل حروف انگلیسی، عدد، نقطه، خط تیره یا زیرخط باشد."
        )
    return username


def validate_password(password: str) -> str:
    """اعتبارسنجی رمز عبور — حداقل ۶ کاراکتر."""
    if len(password) < 6:
        raise ValidationError("رمز عبور باید حداقل ۶ کاراکتر باشد.")
    if len(password) > 128:
        raise ValidationError("رمز عبور نمی‌تواند بیشتر از ۱۲۸ کاراکتر باشد.")
    return password
