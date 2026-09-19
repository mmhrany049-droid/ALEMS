"""منطق دامنه دانش‌آموز — بررسی کامل بودن پروفایل و اعتبارسنجی وضعیت."""
from __future__ import annotations

from app.modules.student.models import StudentProfile
from app.shared.exceptions import ValidationError


def is_profile_complete(profile: StudentProfile | None) -> bool:
    """آیا پروفایل کامل است؟ کاربر بدون پروفایل کامل باید به تکمیل آن هدایت شود."""
    return profile is not None and bool(profile.full_name) and bool(profile.grade) and bool(profile.field)


def validate_energy_level(level: int) -> int:
    """سطح انرژی باید بین ۱ تا ۵ باشد."""
    if not (1 <= level <= 5):
        raise ValidationError("سطح انرژی باید عددی بین ۱ تا ۵ باشد.")
    return level
