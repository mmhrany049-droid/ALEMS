"""مدیریت رویدادهای داخلی — Event Bus سبک (Core System Module).

ماژول‌ها رویدادها را «اعلام» می‌کنند و شنونده‌ها مستقل واکنش نشان می‌دهند.
این سبک وابستگی بین ماژول‌ها را کم می‌کند (مثلاً Activity → Review).
"""
from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("alems.events")

Handler = Callable[[dict[str, Any]], None]


class EventBus:
    """Event Bus داخلی سبک برای اعلام تغییرات مهم بین ماژول‌ها."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    def emit(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        for handler in self._handlers.get(event_name, []):
            try:
                handler(payload)
            except Exception:  # noqa: BLE001 — خطای شنونده نباید مسیر اصلی را بشکند
                logger.exception("خطا در شنونده رویداد %s", event_name)


event_bus = EventBus()
