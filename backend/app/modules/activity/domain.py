"""Activity & Test Engine — pure domain rules, NO I/O (doc 03 §3.1).

doc 08 §8.1 scoring:
    percent_konkur = (C - k*W) / T * 100      (k پیش‌فرض 0.33 از Settings)
    percent_no_penalty = C / T * 100
    T=0 → null · درصد منفی نمایش داده می‌شود (show_negative=true)

doc 08 §8.2 وضعیت پاسخ:
    answered + correct/wrong → پاسخ داد و کلید موجود بود
    unanswered               → آگاهانه نزده
    not_entered              → در past import هنوز وارد نشده

doc 09 §9.2: range + parity (any|odd|even) + count + difficulty.
اگر بعد از فیلتر سوالی نماند: «فقط X سوال با این شرایط وجود دارد.»
"""
from __future__ import annotations

MODES = ("timed", "untimed", "past")
PARITIES = ("any", "odd", "even")
STATUSES = ("answered", "unanswered", "not_entered")
RESULTS = ("correct", "wrong", "blank", "unknown")

# دفترچه خطا — نوع اشتباه (doc 04: Error Notebook)
ERROR_TYPES = ("careless", "concept", "method", "memory", "other")
ERROR_TYPE_LABELS_FA = {
    "careless": "بی‌دقتی",
    "concept": "اشکال مفهومی",
    "method": "روش حل",
    "memory": "فراموشی",
    "other": "سایر",
}

DEFAULT_PENALTY_K = 0.33  # doc 08 §8.1 — پیش‌فرض از Settings

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa_num(value: int | float) -> str:
    """Persian digits for user-facing counts inside messages."""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value).translate(_FA_DIGITS)


def zero_remaining_message(scope_count: int) -> str:
    """doc 09 §9.2 — پیام خطای اجباری وقتی بعد از فیلتر سوالی نمی‌ماند."""
    return f"فقط {fa_num(scope_count)} سوال با این شرایط وجود دارد."


def filter_numbers(numbers: list[int], from_number: int | None, to_number: int | None, parity: str) -> list[int]:
    """range + parity روی شماره سوال‌ها (doc 09 §9.2)."""
    out = []
    for n in numbers:
        if from_number is not None and n < from_number:
            continue
        if to_number is not None and n > to_number:
            continue
        if parity == "odd" and n % 2 == 0:
            continue
        if parity == "even" and n % 2 == 1:
            continue
        out.append(n)
    return out


def normalize_answer(value: str | None) -> str:
    """مقایسه پایدار پاسخ/کلید: trim + یکسان‌سازی حروف عربی و ارقام انگلیسی→فارسی."""
    if value is None:
        return ""
    s = str(value).strip().translate(str.maketrans({"ي": "ی", "ك": "ک", "ة": "ه", "\xa0": " "}))
    return " ".join(s.split()).casefold()


def grade_answer(answer: str | None, key: str | None) -> str:
    """answered + کلید موجود → correct/wrong (doc 08 §8.2)؛ بدون کلید → unknown."""
    if key is None or str(key).strip() == "":
        return "unknown"
    if answer is None or str(answer).strip() == "":
        return "wrong"  # پاسخ داده ولی خالی = غلط
    return "correct" if normalize_answer(answer) == normalize_answer(key) else "wrong"


def result_for(status: str, result: str | None, answer: str | None, key: str | None) -> str:
    """result صریح برنده است؛ وگرنه از status + answer/key استنتاج می‌شود."""
    if result is not None:
        return result
    if status == "unanswered":
        return "blank"
    if status == "not_entered":
        return "unknown"
    return grade_answer(answer, key)


def score_attempts(
    latest: list[tuple[str, str]],
    total: int,
    k: float = DEFAULT_PENALTY_K,
) -> dict:
    """doc 08 §8.1 — scoring با کمترین مجازات konkur.

    latest: [(status, result)] آخرین attempt هر سوال انتخاب‌شده
            (سوال‌های ثبت‌نشده اصلاً در لیست نیستند → unanswered حساب می‌شوند).
    T = total (کل سوال‌های انتخاب‌شده) — نه تعداد attemptها.
    T=0 → percentها null. درصد منفی همان‌طور که هست برمی‌گردد (show_negative).
    """
    correct = sum(1 for _s, r in latest if r == "correct")
    wrong = sum(1 for _s, r in latest if r == "wrong")
    not_entered = sum(1 for s, _r in latest if s == "not_entered")
    unanswered = total - correct - wrong - not_entered
    if unanswered < 0:
        # آخرینattemptها بیش از total (مثلاً past session بزرگ‌تر شده) — total را جلو بکش
        total = correct + wrong + not_entered + 0
        unanswered = 0

    percent_konkur = None
    percent_no_penalty = None
    if total > 0:
        percent_konkur = round((correct - k * wrong) / total * 100, 2)
        percent_no_penalty = round(correct / total * 100, 2)

    return {
        "total_count": total,
        "correct_count": correct,
        "wrong_count": wrong,
        "unanswered_count": unanswered,
        "not_entered_count": not_entered,
        "percent_konkur": percent_konkur,
        "percent_no_penalty": percent_no_penalty,
        "penalty_k": k,
    }
