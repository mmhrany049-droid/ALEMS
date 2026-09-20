"""Event Bus — in-process pub/sub for domain events (doc 03 §3.4).

Minimal event set mandated by the docs:
- test_records.created
- question_marks.changed
- review.completed
- plan.updated
- exam.finished
- checkin.submitted

Consumers (doc 03 §3.4): review rebuild, rewards, analytics cache invalidation.
A failing consumer must never break the producer (exceptions are logged).
"""
from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable

logger = logging.getLogger("alems.events")

TEST_RECORDS_CREATED = "test_records.created"
QUESTION_MARKS_CHANGED = "question_marks.changed"
REVIEW_COMPLETED = "review.completed"
PLAN_UPDATED = "plan.updated"
EXAM_FINISHED = "exam.finished"
CHECKIN_SUBMITTED = "checkin.submitted"

ALL_EVENTS: tuple[str, ...] = (
    TEST_RECORDS_CREATED,
    QUESTION_MARKS_CHANGED,
    REVIEW_COMPLETED,
    PLAN_UPDATED,
    EXAM_FINISHED,
    CHECKIN_SUBMITTED,
)


@dataclass
class Event:
    name: str
    payload: dict[str, Any] = field(default_factory=dict)


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Handler) -> None:
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: Handler) -> None:
        handlers = self._handlers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: Event) -> int:
        """Deliver event to all subscribers; returns number of handlers called."""
        called = 0
        for handler in list(self._handlers.get(event.name, [])):
            called += 1
            try:
                handler(event)
            except Exception:  # pragma: no cover — consumer isolation
                logger.exception("event handler failed for %s", event.name)
        return called


# App-wide bus (modular monolith — single process)
event_bus = EventBus()
