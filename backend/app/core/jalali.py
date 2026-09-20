"""Jalali (Shamsi) calendar — pure functions, no I/O (doc 03 §3.1, §3.5).

Algorithm: Borkowski's Jalaali calendar algorithm — the same one used by
`jalaali-js` (the frontend library mandated by doc 03), so backend and
frontend always agree on the same date. Covered by round-trip +
golden-date + jalaali-js-cross-check tests in tests/test_jalali.py.

Conventions (doc 03 §3.5):
- week starts Saturday: weekday index 0=Saturday … 6=Friday
- "today" is computed in Asia/Tehran
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")

JALALI_MONTHS_FA = (
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
)
WEEKDAYS_FA = ("شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه")
WEEKDAYS_EN = ("Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday")

# 33-year leap-cycle break years (Borkowski) — same table as jalaali-js
BREAKS = (
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181,
    1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
)
MIN_JALAALI_YEAR = BREAKS[0]
MAX_JALAALI_YEAR = BREAKS[-1] - 1


def _div(a: int, b: int) -> int:
    """Truncating division toward zero (JavaScript ~~(a/b) semantics)."""
    q, r = divmod(a, b)
    if r != 0 and (a < 0) != (b < 0):
        q += 1
    return q


def _mod(a: int, b: int) -> int:
    """Non-negative modulo (b > 0) — Python % already has this semantics."""
    return a % b


def jal_cal_core(jy: int) -> tuple[int, int, int, int]:
    """Core of the Borkowski algorithm.

    Returns (gy, march, jump, n):
    - gy: Gregorian year in which the Jalaali year `jy` starts
    - march: day of March on which Farvardin 1 falls (20/21/22/23)
    - jump, n: cycle length and offset inside the 33-year cycle
    """
    if not (MIN_JALAALI_YEAR <= jy <= MAX_JALAALI_YEAR):
        raise ValueError(f"Jalaali year {jy} out of supported range [{MIN_JALAALI_YEAR}, {MAX_JALAALI_YEAR}]")
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    jump = 0
    for i in range(1, len(BREAKS)):
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j = leap_j + _div(jump, 33) * 8 + _mod(jump, 33) // 4
        jp = jm
    n = jy - jp
    leap_j = leap_j + _div(n, 33) * 8 + (_mod(n, 33) + 3) // 4
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    return gy, march, jump, n


def _leap_from_cycle(jump: int, n: int) -> int:
    """0 => current year is leap; 1..4 => years since the last leap year."""
    adjusted = n
    if jump - n < 6:
        adjusted = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(adjusted + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap


def jal_cal(jy: int) -> tuple[int, int, int]:
    """(leap, gy, march) — Farvardin 1 of Jalaali year jy."""
    gy, march, jump, n = jal_cal_core(jy)
    return _leap_from_cycle(jump, n), gy, march


def jal_cal_short(jy: int) -> tuple[int, int]:
    """(gy, march) without the leap computation."""
    gy, march, _, _ = jal_cal_core(jy)
    return gy, march


# --- Julian Day number conversions (same formulas as jalaali-js) -------------

def g2d(gy: int, gm: int, gd: int) -> int:
    """Gregorian (gy, gm, gd) -> Julian Day number (noon UT)."""
    d = (
        _div((gy + _div(gm - 8, 6) + 100100) * 1461, 4)
        + _div(153 * _mod(gm + 9, 12) + 2, 5)
        + gd
        - 34840408
    )
    d = d - _div(_div(gy + 100100 + _div(gm - 8, 6), 100) * 3, 4) + 752
    return d


def d2g(jdn: int) -> tuple[int, int, int]:
    """Julian Day number -> (gy, gm, gd)."""
    j = 4 * jdn + 139361631
    j = j + _div(_div(4 * jdn + 183187720, 146097) * 3, 4) * 4 - 3908
    i = _mod(j, 1461) // 4 * 5 + 308
    gd = _mod(i, 153) // 5 + 1
    gm = _mod(_div(i, 153), 12) + 1
    gy = _div(j, 1461) - 100100 + _div(8 - gm, 6)
    return gy, gm, gd


def j2d(jy: int, jm: int, jd: int) -> int:
    """Jalali (jy, jm, jd) -> Julian Day number (noon UT)."""
    gy, march = jal_cal_short(jy)
    return g2d(gy, 3, march) + (jm - 1) * 31 - _div(jm, 7) * (jm - 7) + jd - 1


def d2j(jdn: int) -> tuple[int, int, int]:
    """Julian Day number -> (jy, jm, jd)."""
    gy = d2g(jdn)[0]
    jy = min(gy - 621, MAX_JALAALI_YEAR)
    leap, gy_j, march = jal_cal(jy)
    jdn1f = g2d(gy_j, 3, march)
    k = jdn - jdn1f
    if k >= 0:
        if k <= 185:
            return jy, 1 + _div(k, 31), _mod(k, 31) + 1
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    return jy, 7 + _div(k, 30), _mod(k, 30) + 1


# --- public conversions -------------------------------------------------------

def gregorian_to_jalali(year: int, month: int, day: int) -> tuple[int, int, int]:
    """(gy, gm, gd) -> (jy, jm, jd)."""
    return d2j(g2d(year, month, day))


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> tuple[int, int, int]:
    """(jy, jm, jd) -> (gy, gm, gd)."""
    return d2g(j2d(jy, jm, jd))


def is_jalali_leap_year(jy: int) -> bool:
    """True when Esfand has 30 days (year is kabise/leap)."""
    return _leap_from_cycle(*jal_cal_core(jy)[2:]) == 0


def jalali_month_days(jy: int, jm: int) -> int:
    """Days in Jalali month jm (1-12) of year jy: 31 for 1-6, 30 for 7-11, 29/30 for 12."""
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap_year(jy) else 29


def jalali_weekday(jy: int, jm: int, jd: int) -> int:
    """0=Saturday … 6=Friday (doc 03 §3.5)."""
    gy, gm, gd = d2g(j2d(jy, jm, jd))
    p = dt.date(gy, gm, gd).weekday()  # Mon=0 .. Sun=6
    return (p + 2) % 7  # -> Sat=0, Sun=1, Mon=2, .., Fri=6


def week_start(jalali_date: "JalaliDate") -> "JalaliDate":
    """Saturday of the week containing jalali_date (weekday 0=Saturday)."""
    shift = jalali_weekday(jalali_date.year, jalali_date.month, jalali_date.day)
    g = _from_jalali(jalali_date.year, jalali_date.month, jalali_date.day)
    return _to_jalali(g - dt.timedelta(days=shift))


def week_days(week_start_date: "JalaliDate") -> list["JalaliDate"]:
    """The 7 days Saturday..Friday of the week."""
    start_g = _from_jalali(week_start_date.year, week_start_date.month, week_start_date.day)
    return [_to_jalali(start_g + dt.timedelta(days=i)) for i in range(7)]


@dataclass(frozen=True)
class JalaliDate:
    """A date in the Jalali calendar."""

    year: int
    month: int
    day: int

    def to_jalali_tuple(self) -> tuple[int, int, int]:
        return self.year, self.month, self.day

    @property
    def weekday(self) -> int:
        """0=Saturday … 6=Friday."""
        return jalali_weekday(self.year, self.month, self.day)

    @property
    def weekday_fa(self) -> str:
        return WEEKDAYS_FA[self.weekday]

    @property
    def month_fa(self) -> str:
        return JALALI_MONTHS_FA[self.month - 1]

    def to_gregorian(self) -> dt.date:
        gy, gm, gd = jalali_to_gregorian(self.year, self.month, self.day)
        return dt.date(gy, gm, gd)

    def format(self) -> str:
        """e.g. 1405/06/29"""
        return f"{self.year:04d}/{self.month:02d}/{self.day:02d}"

    def format_long_fa(self) -> str:
        """e.g. ۲۹ شهریور ۱۴۰۵"""
        return f"{_fa_digit(self.day)} {self.month_fa} {_fa_digit(self.year)}"


def _to_jalali(g: dt.date) -> JalaliDate:
    jy, jm, jd = gregorian_to_jalali(g.year, g.month, g.day)
    return JalaliDate(jy, jm, jd)


def _from_jalali(jy: int, jm: int, jd: int) -> dt.date:
    gy, gm, gd = jalali_to_gregorian(jy, jm, jd)
    return dt.date(gy, gm, gd)


def today_jalali(now: dt.datetime | None = None) -> JalaliDate:
    """Today in Asia/Tehran (doc 03 §3.5). `now` may be any aware datetime."""
    tz_now = (now or dt.datetime.now(tz=TEHRAN)).astimezone(TEHRAN)
    return _to_jalali(tz_now.date())


def fa_digit(text: str) -> str:
    """Latin digits -> Persian digits (UI is Persian-first). U+06F0..U+06F9."""
    mapping = str.maketrans("0123456789", "".join(chr(0x06F0 + i) for i in range(10)))
    return text.translate(mapping)


def _fa_digit(n: int) -> str:
    return fa_digit(str(n))
