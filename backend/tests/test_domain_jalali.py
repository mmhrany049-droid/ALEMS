"""تست‌های واحد تقویم جلالی و هفته ایرانی."""
from __future__ import annotations

import datetime as dt

import pytest

from app.core.jalali import (
    JALALI_MONTHS,
    format_jalali,
    format_jalali_long,
    is_jalali_leap,
    jalali_month_length,
    jalali_month_range,
    jalali_to_gregorian,
    jalali_weekday,
    to_jalali,
    week_end,
    week_start,
)


class TestJalaliConversion:
    def test_known_date_nowruz(self):
        # ۱۴۰۴/۰۱/۰۱ = 2025-03-21
        assert to_jalali(dt.date(2025, 3, 21)) == (1404, 1, 1)

    def test_known_date_doc(self):
        # ۱۴۰۵/۰۶/۲۸ = 2026-09-19 (امروز — معادل جلالی صحیح)
        assert to_jalali(dt.date(2026, 9, 19)) == (1405, 6, 28)
        # ۱۴۰۴/۰۶/۲۸ = 2025-09-19
        assert to_jalali(dt.date(2025, 9, 19)) == (1404, 6, 28)

    def test_roundtrip(self):
        # رفت و برگشت برای چند تاریخ
        for g in [dt.date(2024, 3, 20), dt.date(2025, 12, 31), dt.date(2026, 7, 10),
                  dt.date(2023, 8, 22), dt.date(2027, 2, 19)]:
            jy, jm, jd = to_jalali(g)
            assert jalali_to_gregorian(jy, jm, jd) == g

    def test_month_lengths(self):
        assert jalali_month_length(1404, 1) == 31
        assert jalali_month_length(1404, 6) == 31
        assert jalali_month_length(1404, 11) == 30
        assert jalali_month_length(1404, 12) == 29  # ۱۴۰۴ کبیسه نیست؟ بررسی رفت‌وبرگشت بالا ملاک است

    def test_leap_year(self):
        # 1403 کبیسه است (اسفند ۳۰ روز)
        assert jalali_month_length(1403, 12) == 30

    def test_month_range(self):
        rng = jalali_month_range(1404, 6)
        assert to_jalali(rng.start) == (1404, 6, 1)
        assert to_jalali(rng.end) == (1404, 6, 31)

    def test_persian_labels(self):
        assert JALALI_MONTHS[0] == "فروردین"
        assert JALALI_MONTHS[5] == "شهریور"
        date = dt.date(2025, 9, 19)
        assert format_jalali(date) == "1404/06/28"  # 2025-09-19
        assert "شهریور" in format_jalali_long(date)


class TestIranianWeek:
    """هفته: شنبه تا جمعه — ۰=شنبه ... ۶=جمعه"""

    def test_weekday_mapping(self):
        # 2026-09-19 شنبه است
        assert jalali_weekday(dt.date(2026, 9, 19)) == 0
        # 2026-09-20 یکشنبه
        assert jalali_weekday(dt.date(2026, 9, 20)) == 1
        # 2026-09-25 جمعه
        assert jalali_weekday(dt.date(2026, 9, 25)) == 6

    def test_week_start_is_saturday(self):
        for offset in range(7):
            day = dt.date(2026, 9, 19) + dt.timedelta(days=offset)
            start = week_start(day)
            assert jalali_weekday(start) == 0
            assert start == dt.date(2026, 9, 19)

    def test_week_end_is_friday(self):
        end = week_end(dt.date(2026, 9, 22))
        assert jalali_weekday(end) == 6
        assert end == dt.date(2026, 9, 25)
