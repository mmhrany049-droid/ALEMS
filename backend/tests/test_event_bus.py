"""Event bus (doc 03 §3.4) — publish/subscribe + consumer isolation."""
from __future__ import annotations

from app.core.events import (
    ALL_EVENTS,
    Event,
    EventBus,
    REVIEW_COMPLETED,
)


def test_all_mandated_events_defined():
    assert set(ALL_EVENTS) == {
        "test_records.created",
        "question_marks.changed",
        "review.completed",
        "plan.updated",
        "exam.finished",
        "checkin.submitted",
    }


def test_publish_subscribes_and_delivers():
    bus = EventBus()
    got = []
    bus.subscribe(REVIEW_COMPLETED, lambda e: got.append(e.payload))
    n = bus.publish(Event(REVIEW_COMPLETED, {"review_id": "abc"}))
    assert n == 1
    assert got == [{"review_id": "abc"}]


def test_unsubscribe_stops_delivery():
    bus = EventBus()
    got = []
    h = lambda e: got.append(1)  # noqa: E731
    bus.subscribe(REVIEW_COMPLETED, h)
    bus.unsubscribe(REVIEW_COMPLETED, h)
    bus.publish(Event(REVIEW_COMPLETED, {}))
    assert got == []


def test_failing_consumer_does_not_break_others():
    bus = EventBus()
    got = []

    def bad(e):
        raise RuntimeError("boom")

    bus.subscribe(REVIEW_COMPLETED, bad)
    bus.subscribe(REVIEW_COMPLETED, lambda e: got.append("ok"))
    # must not raise
    n = bus.publish(Event(REVIEW_COMPLETED, {}))
    assert n == 2
    assert got == ["ok"]
