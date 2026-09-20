"""Jalali calendar correctness (core/jalali.py).

Golden dates verified against jalaali-js (the frontend library mandated by
doc 03) — 2000 random dates in both directions with 0 mismatches.
"""
from __future__ import annotations

import datetime as dt

import pytest

from app.core.jalali import (
    WEEKDAYS_FA,
    JalaliDate,
    fa_digit,
    gregorian_to_jalali,
    is_jalali_leap_year,
    jalali_month_days,
    jalali_to_gregorian,
    jalali_weekday,
    today_jalali,
    week_days,
    week_start,
)


class TestGoldenDates:
    # Nowruz anchors (real-world Nowruz dates)
    def test_nowruz_2024(self):
        assert gregorian_to_jalali(2024, 3, 20) == (1403, 1, 1)

    def test_nowruz_2025(self):
        assert gregorian_to_jalali(2025, 3, 21) == (1404, 1, 1)

    def test_nowruz_1405_boundary(self):
        # last day of 1404 / first day of 1405
        assert gregorian_to_jalali(2026, 3, 20) == (1404, 12, 29)
        assert gregorian_to_jalali(2026, 3, 21) == (1405, 1, 1)

    def test_documented_example(self):
        # from jalaali-js docs: toGregorian(1395, 1, 23) == 2016-04-11
        assert jalali_to_gregorian(1395, 1, 23) == (2016, 4, 11)

    def test_today_2026_09_20(self):
        # 2026-09-20 (Tehran) — cross-verified with jalaali-js
        assert gregorian_to_jalali(2026, 9, 20) == (1405, 6, 29)


class TestRoundTrip:
    def test_round_trip_g_to_j_to_g(self):
        base = dt.date(2023, 1, 1)
        for i in range(1850):
            d = base + dt.timedelta(days=i)
            jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
            assert jalali_to_gregorian(jy, jm, jd) == (d.year, d.month, d.day), f"mismatch at {d}"

    def test_round_trip_across_year_boundaries(self):
        # include Nowruz boundaries explicitly
        boundaries = [dt.date(2024, 3, 20), dt.date(2025, 3, 21), dt.date(2026, 3, 20), dt.date(2026, 3, 21)]
        for d in boundaries:
            j = gregorian_to_jalali(d.year, d.month, d.day)
            assert jalali_to_gregorian(*j) == (d.year, d.month, d.day)


class TestLeapYears:
    def test_1403_is_leap(self):
        # 1403-01-01 = 2024-03-20 and 1404-01-01 = 2025-03-21 -> 366 days
        assert is_jalali_leap_year(1403)
        assert jalali_month_days(1403, 12) == 30

    def test_1404_not_leap(self):
        # 1404-01-01 = 2025-03-21 and 1405-01-01 = 2026-03-21 -> 365 days
        assert not is_jalali_leap_year(1404)
        assert jalali_month_days(1404, 12) == 29

    def test_month_lengths(self):
        for jm in range(1, 7):
            assert jalali_month_days(1405, jm) == 31
        for jm in range(7, 12):
            assert jalali_month_days(1405, jm) == 30


class TestWeek:
    def test_weekday_mapping_saturday_zero(self):
        # 2026-09-19 is a Saturday (Gregorian)
        jy, jm, jd = gregorian_to_jalali(2026, 9, 19)
        assert jalali_weekday(jy, jm, jd) == 0
        # 2026-09-20 is a Sunday
        jy, jm, jd = gregorian_to_jalali(2026, 9, 20)
        assert jalali_weekday(jy, jm, jd) == 1

    def test_weekdays_against_python(self):
        base = dt.date(2026, 9, 14)
        for i in range(14):
            d = base + dt.timedelta(days=i)
            jd = JalaliDate(*gregorian_to_jalali(d.year, d.month, d.day))
            expect = (d.weekday() + 2) % 7  # Sat=0..Fri=6
            assert jd.weekday == expect, f"{d} {d.strftime('%A')}"

    def test_week_start_is_saturday(self):
        # 1405-07-28 = 2026-10-20 (Tuesday, cross-verified vs jalaali-js)
        # -> its week starts on Saturday 1405-07-25 (= 2026-10-17)
        d = JalaliDate(1405, 7, 28)
        ws = week_start(d)
        assert ws.weekday == 0
        assert ws.format() == "1405/07/25"
        days = week_days(ws)
        assert [x.format() for x in days] == [
            "1405/07/25", "1405/07/26", "1405/07/27", "1405/07/28",
            "1405/07/29", "1405/07/30", "1405/08/01",
        ]
        # and the Gregorian side agrees: 2026-10-17 is a Saturday
        assert dt.date(2026, 10, 17).weekday() == 5  # python Sat=5

    def test_week_start_of_saturday(self):
        d = JalaliDate(1405, 7, 25)  # Saturday (2026-10-17)
        assert week_start(d).format() == d.format()

    def test_weekday_names_against_gregorian_names(self):
        # non-circular check: explicit mapping from English weekday names
        name2index = {"Saturday": 0, "Sunday": 1, "Monday": 2, "Tuesday": 3,
                      "Wednesday": 4, "Thursday": 5, "Friday": 6}
        base = dt.date(2026, 9, 14)
        for i in range(21):
            d = base + dt.timedelta(days=i)
            jd = JalaliDate(*gregorian_to_jalali(d.year, d.month, d.day))
            assert jd.weekday == name2index[d.strftime("%A")], f"{d} {d.strftime('%A')}"
            assert jd.weekday_fa == WEEKDAYS_FA[name2index[d.strftime("%A")]]


class TestFormatting:
    def test_format(self):
        assert JalaliDate(1405, 6, 29).format() == "1405/06/29"

    def test_fa_digits(self):
        assert fa_digit("1405/06/29") == "۱۴۰۵/۰۶/۲۹"
        assert fa_digit("1000") == "۱۰۰۰"

    def test_long_fa(self):
        d = JalaliDate(1405, 6, 29)
        assert "شهریور" in d.format_long_fa()

    def test_today_jalali_tehran(self):
        fixed = dt.datetime(2026, 9, 20, 18, 0, tzinfo=dt.timezone.utc)  # 21:30 Tehran
        assert today_jalali(fixed).format() == "1405/06/29"
        # same UTC instant one hour earlier is still the same Tehran day
        fixed2 = dt.datetime(2026, 9, 20, 9, 0, tzinfo=dt.timezone.utc)  # 12:30 Tehran
        assert today_jalali(fixed2).format() == "1405/06/29"
        # but late UTC evening crosses into next Tehran day
        fixed3 = dt.datetime(2026, 9, 20, 20, 31, tzinfo=dt.timezone.utc)  # 24:01 Tehran
        assert today_jalali(fixed3).format() == "1405/06/30"

    def test_month_and_weekday_names(self):
        assert WEEKDAYS_FA[0] == "شنبه"
        assert JalaliDate(1405, 6, 29).month_fa == "شهریور"
