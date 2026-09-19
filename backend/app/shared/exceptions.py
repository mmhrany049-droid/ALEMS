"""خطاهای مشترک — همه پیام‌ها فارسی و خوانا هستند."""
from __future__ import annotations

from typing import Any


class AlemsError(Exception):
    """خطای پایه ALEMS با کد و پیام فارسی."""

    status_code: int = 400
    code: str = "ALEMS_ERROR"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None,
                 code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code


class ValidationError(AlemsError):
    status_code = 422
    code = "VALIDATION_ERROR"


class NotFoundError(AlemsError):
    status_code = 404
    code = "NOT_FOUND"


class UnauthorizedError(AlemsError):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AlemsError):
    status_code = 403
    code = "FORBIDDEN"


class ConflictError(AlemsError):
    status_code = 409
    code = "CONFLICT"
