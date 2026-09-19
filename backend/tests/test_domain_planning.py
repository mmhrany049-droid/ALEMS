"""تست‌های واحد دامنه برنامه‌ریزی — زمان‌های آزاد و تولید برنامه هفتگی."""
from __future__ import annotations

import datetime as dt

from app.modules.planning.domain import (
    OccupiedBlock,
    PlanningPolicy,
    free_windows,
    generate_week_plan,
    summarize_week_items,
)


def _t(hhmm: str) -> dt.time:
    h, m = hhmm.split(":")
    return dt.time(int(h), int(m))


class TestFreeWindows:
    def test_no_occupied_full_day(self):
        windows = free_windows([])
        assert windows[0][0] == dt.time(6, 0)

    def test_school_block(self):
        # مدرسه ۷:۳۰ تا ۱۳:۳۰ → صبح و بعدازظهر آزاد
        windows = free_windows([OccupiedBlock(_t("07:30"), _t("13:30"))])
        assert windows[0] == (dt.time(6, 0), dt.time(7, 30))
        assert windows[1] == (dt.time(13, 30), dt.time(23, 30))

    def test_class_block_overlap(self):
        windows = free_windows([
            OccupiedBlock(_t("07:30"), _t("13:30")),
            OccupiedBlock(_t("16:00"), _t("18:00")),
        ])
        assert (dt.time(13, 30), dt.time(16, 0)) in windows

    def test_invalid_range_skipped(self):
        # بازه معکوس نادیده گرفته می‌شود
        windows = free_windows([OccupiedBlock(_t("13:00"), _t("08:00"))])
        assert len(windows) == 1


class TestWeekPlanGeneration:
    def test_generates_for_all_7_days(self):
        plan = generate_week_plan(
            week_start=dt.date(2026, 9, 19),
            occupied_by_day={},
            goals=[{"title": "ریاضی - حد", "subject": "حسابان", "minutes": 90}],
        )
        assert set(plan.keys()) == set(range(7))  # شنبه تا جمعه

    def test_school_days_have_fewer_items(self):
        policy = PlanningPolicy(session_minutes=45, break_minutes=15, max_daily_items=100)
        occupied = {
            0: [OccupiedBlock(_t("07:30"), _t("13:30"))],  # شنبه مدرسه
            1: [],  # یکشنبه آزاد کامل
        }
        plan = generate_week_plan(
            week_start=dt.date(2026, 9, 19),
            occupied_by_day=occupied,
            goals=[{"title": "درس", "minutes": 100000}],
            policy=policy,
        )
        # روز آزاد باید آیتم‌های بیشتری داشته باشد
        assert len(plan[1]) > len(plan[0])

    def test_respects_max_daily_items(self):
        policy = PlanningPolicy(max_daily_items=2)
        plan = generate_week_plan(
            week_start=dt.date(2026, 9, 19),
            occupied_by_day={},
            goals=[{"title": "درس", "minutes": 100000}],
            policy=policy,
        )
        assert all(len(items) <= 2 for items in plan.values())

    def test_summary_minutes(self):
        summary = summarize_week_items([
            {"start": "16:00", "end": "17:00", "title": "ریاضی", "subject": "حسابان"},
            {"start": "18:00", "end": "18:30", "title": "فیزیک", "subject": "فیزیک"},
        ])
        assert summary["total_minutes"] == 90
        assert summary["by_subject"]["حسابان"] == 60
