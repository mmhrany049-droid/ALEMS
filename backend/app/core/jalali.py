"""تبدیل تقویم جلالی (شمسی) — پیاده‌سازی الگوریتم استاندارد jalaali.

این ماژول بخشی از Domain است: منطق خالص تقویم بدون وابستگی به دیتابیس یا فریم‌ورک.
هفته ایرانی: شنبه (day_of_week=0) تا جمعه (day_of_week=6).
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass


def _div(a: int, b: int) -> int:
    """تقسیم صحیح به سمت صفر (مطابق jalaali-js)."""
    return int(a / b) if (a >= 0) == (b > 0) else -int(-a / b)


def _mod(a: int, b: int) -> int:
    return a - _div(a, b) * b


# ---------- الگوریتم جلالی (jalCal از jalaali-js) ----------

BREAKS = [
    -61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210,
    1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178,
]


def _jal_cal(jy: int) -> tuple[int, int]:
    """خروجی: (leap، march) — leap: فاصله تا آخرین سال کبیسه، march: روز گregexp\
    اسفند/مارس معادل ۱ فروردین."""
    bl = len(BREAKS)
    gy = jy + 621
    leap_j = -14
    jp = BREAKS[0]
    if jy < jp or jy >= BREAKS[bl - 1]:
        raise ValueError(f"سال جلالی خارج از محدوده: {jy}")
    jump = 0
    for i in range(1, bl):
        jm = BREAKS[i]
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        jp = jm
    n = jy - jp

    leap_j += _div(n, 33) * 8 + _div(_mod(n, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - n == 4:
        leap_j += 1

    leap_g = _div(gy, 4) - _div((_div(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g

    if jump - n < 6:
        n = n - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(n + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, march


# ---------- تبدیل JDN ↔ میلادی (الگوریتم استاندارد) ----------

def g2d(gy: int, gm: int, gd: int) -> int:
    """تاریخ میلادی → شماره روز ژولینی (JDN)."""
    a = _div(14 - gm, 12)
    y = gy + 4800 - a
    m = gm + 12 * a - 3
    return gd + _div(153 * m + 2, 5) + 365 * y + _div(y, 4) - _div(y, 100) + _div(y, 400) - 32045


def d2g(jdn: int) -> tuple[int, int, int]:
    """JDN → (سال، ماه، روز) میلادی."""
    a = jdn + 32044
    b = _div(4 * a + 3, 146097)
    c = a - _div(146097 * b, 4)
    d = _div(4 * c + 3, 1461)
    e = c - _div(1461 * d, 4)
    m = _div(5 * e + 2, 153)
    day = e - _div(153 * m + 2, 5) + 1
    month = m + 3 - 12 * _div(m, 10)
    year = 100 * b + d - 4800 + _div(m, 10)
    return year, month, day


# ---------- تبدیل جلالی ↔ JDN ----------

def j2d(jy: int, jm: int, jd: int) -> int:
    """تاریخ جلالی → JDN."""
    _leap, march = _jal_cal(jy)
    return g2d(jy + 621, 3, march) + (jm - 1) * 31 - (jm // 7) * (jm - 7) + jd - 1


def d2j(jdn: int) -> tuple[int, int, int]:
    """JDN → (سال، ماه، روز) جلالی."""
    gy = d2g(jdn)[0]
    jy = gy - 621
    leap, march = _jal_cal(jy)
    jdn1f = g2d(gy, 3, march)
    k = jdn - jdn1f
    if k >= 0:
        if k <= 185:
            jm = 1 + _div(k, 31)
            jd = _mod(k, 31) + 1
            return jy, jm, jd
        k -= 186
    else:
        jy -= 1
        k += 179
        if leap == 1:
            k += 1
    jm = 7 + _div(k, 30)
    jd = _mod(k, 30) + 1
    return jy, jm, jd


# ---------- API عمومی ----------

def to_jalali(date: dt.date) -> tuple[int, int, int]:
    """تبدیل تاریخ میلادی به (سال، ماه، روز) جلالی."""
    return d2j(g2d(date.year, date.month, date.day))


def jalali_to_gregorian(jy: int, jm: int, jd: int) -> dt.date:
    """تبدیل (سال، ماه، روز) جلالی به تاریخ میلادی."""
    y, m, d = d2g(j2d(jy, jm, jd))
    return dt.date(y, m, d)


def is_jalali_leap(jy: int) -> bool:
    return _jal_cal(jy)[0] == 0


def jalali_month_length(jy: int, jm: int) -> int:
    if jm <= 6:
        return 31
    if jm <= 11:
        return 30
    return 30 if is_jalali_leap(jy) else 29


# ---------- نام‌های فارسی ----------

JALALI_MONTHS = [
    "فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
    "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند",
]

# روزهای هفته ایرانی — شنبه تا جمعه
WEEKDAY_NAMES = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]


def jalali_weekday(date: dt.date) -> int:
    """شماره روز هفته ایرانی: ۰=شنبه ... ۶=جمعه.

    Python: دوشنبه=۰ ... یکشنبه=۶ → نگاشت: (weekday + 2) % 7
    """
    return (date.weekday() + 2) % 7


def week_start(date: dt.date) -> dt.date:
    """شنبه‌ی همان هفته (ابتدای هفته ایرانی)."""
    return date - dt.timedelta(days=jalali_weekday(date))


def week_end(date: dt.date) -> dt.date:
    """جمعه‌ی همان هفته (انتهای هفته ایرانی)."""
    return week_start(date) + dt.timedelta(days=6)


def format_jalali(date: dt.date | None, with_weekday: bool = False) -> str:
    """قالب استاندارد نمایش: ۱۴۰۴/۰۶/۲۸ (اختیاری با نام روز هفته)."""
    if date is None:
        return ""
    jy, jm, jd = to_jalali(date)
    base = f"{jy}/{jm:02d}/{jd:02d}"
    if with_weekday:
        base = f"{WEEKDAY_NAMES[jalali_weekday(date)]} {base}"
    return base


def format_jalali_long(date: dt.date | None) -> str:
    """قالب بلند فارسی: ۲۸ شهریور ۱۴۰۴."""
    if date is None:
        return ""
    jy, jm, jd = to_jalali(date)
    return f"{jd} {JALALI_MONTHS[jm - 1]} {jy}"


@dataclass(frozen=True)
class JalaliMonthRange:
    """بازه میلادی معادل یک ماه جلالی (inclusive)."""
    start: dt.date
    end: dt.date
    year: int
    month: int


def jalali_month_range(jy: int, jm: int) -> JalaliMonthRange:
    """بازه میلادی (inclusive) معادل یک ماه جلالی — برای گزارش ماهانه."""
    start = jalali_to_gregorian(jy, jm, 1)
    end = jalali_to_gregorian(jy, jm, jalali_month_length(jy, jm))
    return JalaliMonthRange(start=start, end=end, year=jy, month=jm)
