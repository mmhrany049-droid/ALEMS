"""Response envelope (doc 06) — every API answer uses the same shape.

Success:
    {"success": true,  "data": {...}, "error": null, "meta": {...}}
Error:
    {"success": false, "data": null, "error": {"code": "...", "message": "فارسی", "details": {...}}}

Rules (user non-negotiable #7): error messages are Persian and actionable.
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# --- codes (stable machine codes; message is the Persian, human-facing text)
E_VALIDATION = "VALIDATION_ERROR"
E_NOT_FOUND = "NOT_FOUND"
E_CONFLICT = "CONFLICT"
E_UNAUTHORIZED = "UNAUTHORIZED"
E_FORBIDDEN = "FORBIDDEN"
E_INTERNAL = "INTERNAL_ERROR"

_PERSIAN_MESSAGES: dict[str, str] = {
    E_VALIDATION: "ورودی‌ها درست نیستند.",
    E_NOT_FOUND: "عناصر مورد نظر پیدا نشد.",
    E_CONFLICT: "این عمل با داده‌های فعلی تداخل دارد.",
    E_UNAUTHORIZED: "برای ادامه باید وارد شوید.",
    E_FORBIDDEN: "دسترسی لازم را ندارید.",
    E_INTERNAL: "خطایی پیش آمد؛ لطفاً دوباره تلاش کنید.",
}


def ok(data: Any = None, meta: dict | None = None) -> dict:
    return {
        "success": True,
        "data": jsonable_encoder(data) if data is not None else {},
        "error": None,
        "meta": meta or {},
    }


def error_body(code: str, message: str | None = None, details: dict | None = None) -> dict:
    return {
        "success": False,
        "data": None,
        "error": {
            "code": code,
            "message": message or _PERSIAN_MESSAGES.get(code, _PERSIAN_MESSAGES[E_INTERNAL]),
            "details": details or {},
        },
        "meta": {},
    }


def error_response(
    status_code: int,
    code: str,
    message: str | None = None,
    details: dict | None = None,
) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=error_body(code, message, details))


# --- exception handlers -----------------------------------------------------

_STATUS_CODE_MAP = {
    400: E_VALIDATION,
    401: E_UNAUTHORIZED,
    403: E_FORBIDDEN,
    404: E_NOT_FOUND,
    409: E_CONFLICT,
}

# framework default English details -> Persian (app-level Persian details win)
_FRAMEWORK_DETAILS_FA = {
    "Not Found": "عناصر مورد نظر پیدا نشد.",
    "Method Not Allowed": "این عمل روی مسیر انتخابی مجاز نیست.",
}


def _code_for_status(status_code: int) -> str:
    return _STATUS_CODE_MAP.get(status_code, E_INTERNAL)


def _persian_message(detail, status_code: int) -> str | None:
    """Prefer an app-provided (Persian) detail; translate framework defaults."""
    if isinstance(detail, str):
        if detail in _FRAMEWORK_DETAILS_FA:
            return _FRAMEWORK_DETAILS_FA[detail]
        return detail  # app raised with its own (Persian) message
    return _PERSIAN_MESSAGES.get(_code_for_status(status_code))


def register_envelope_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = _code_for_status(exc.status_code)
        return error_response(exc.status_code, code, _persian_message(exc.detail, exc.status_code))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            E_VALIDATION,
            "ورودی‌ها درست نیستند.",
            details={"errors": jsonable_encoder(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):  # noqa: BLE001
        import logging

        logging.getLogger("alems").exception("unhandled error on %s %s", request.method, request.url.path)
        return error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            E_INTERNAL,
            "خطایی پیش آمد؛ لطفاً دوباره تلاش کنید.",
        )
