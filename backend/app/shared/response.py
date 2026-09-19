"""پاکت استاندارد پاسخ — مطابق 06_API_CONTRACT.md

تمام پاسخ‌ها با ساختار زیر برگردانده می‌شوند:
    { "success": true, "data": ..., "error": null, "meta": {...} }
"""
from __future__ import annotations

import math
from typing import Any

from fastapi import Query
from pydantic import BaseModel

from app.shared.exceptions import AlemsError


def ok(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """پاسخ موفق استاندارد."""
    return {"success": True, "data": data, "error": None, "meta": meta or {}}


def fail(error: AlemsError) -> dict[str, Any]:
    """پاسخ خطای استاندارد."""
    return {
        "success": False,
        "data": None,
        "error": {"code": error.code, "message": error.message, "details": error.details},
    }


class PageParams:
    """پارامترهای صفحه‌بندی — برای لیست‌های طولانی الزامی است."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="شماره صفحه"),
        page_size: int = Query(20, ge=1, le=200, description="تعداد در هر صفحه"),
    ) -> None:
        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def meta(self, total: int) -> dict[str, Any]:
        return {
            "page": self.page,
            "page_size": self.page_size,
            "total": total,
            "total_pages": max(1, math.ceil(total / self.page_size)),
        }


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
