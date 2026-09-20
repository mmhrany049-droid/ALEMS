"""Settings — pure domain rules, NO I/O (doc 03 §3.1).

سیاست‌ها بدون hard-code (doc 04 Settings): k جریمه کنکور (doc 08 §8.1)،
چرخه مرور [1,3,7,14] (doc 10 §10.2)، سقف روزانه مرور ۲۵ و حداقل خوشه ۸
(doc 10 §10.3)، include_blank_in_review (doc 08 §8.4).
"""
from __future__ import annotations

DEFAULT_REVIEW_INTERVALS = [1, 3, 7, 14]  # doc 10 §10.2
DEFAULT_INCLUDE_BLANK = False             # doc 08 §8.4 — blank اختیاری از settings
DEFAULT_MAX_DAILY_REVIEW = 25             # doc 10 §10.3
DEFAULT_MIN_CLUSTER = 8                   # doc 10 §10.3
DEFAULT_PENALTY_K = 0.33                  # doc 08 §8.1
DEFAULT_STREAK_GRACE_DAYS = 0             # doc 13.2 — از دست دادن روز → reset (grace=0 پیش‌فرض)
STREAK_GRACE_MAX = 7
DEFAULT_AUTO_BACKUP = False              # doc 04 — پشتیبان خودکار در startup


def validate_settings(data: dict) -> list[str]:
    """Persian error list (empty when valid)."""
    errors: list[str] = []

    if "review_intervals" in data and data["review_intervals"] is not None:
        iv = data["review_intervals"]
        ok = (
            isinstance(iv, list)
            and len(iv) > 0
            and all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in iv)
        )
        if not ok:
            errors.append("چرخه مرور باید فهرستی غیرخالی از اعداد مثبت (روز) باشد؛ مثال: [1, 3, 7, 14].")

    if "max_daily_review" in data and data["max_daily_review"] is not None:
        v = data["max_daily_review"]
        if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 100):
            errors.append("سقف مرور روزانه باید عددی بین ۱ تا ۱۰۰ باشد.")

    if "min_cluster" in data and data["min_cluster"] is not None:
        v = data["min_cluster"]
        if not isinstance(v, int) or isinstance(v, bool) or not (1 <= v <= 50):
            errors.append("حداقل اندازه خوشه باید عددی بین ۱ تا ۵۰ باشد.")

    if "konkurs_penalty_k" in data and data["konkurs_penalty_k"] is not None:
        v = data["konkurs_penalty_k"]
        if not isinstance(v, (int, float)) or isinstance(v, bool) or not (0 <= float(v) <= 1):
            errors.append("ضریب جریمه کنکور باید عددی بین ۰ و ۱ باشد.")

    if "auto_backup" in data and data["auto_backup"] is not None:
        v = data["auto_backup"]
        if not isinstance(v, bool):
            errors.append("auto_backup باید true یا false باشد.")

    if "streak_grace_days" in data and data["streak_grace_days"] is not None:
        g = data["streak_grace_days"]
        if not isinstance(g, int) or isinstance(g, bool) or not (0 <= g <= STREAK_GRACE_MAX):
            errors.append(f"روزهای ارفاق پیوستگی باید عدد صحیح بین ۰ و {STREAK_GRACE_MAX} باشد.")

    return errors
