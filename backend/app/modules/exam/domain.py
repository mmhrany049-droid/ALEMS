"""منطق دامنه نمره‌دهی (Scoring Module) — فرمول‌های کنکور.

قوانین ۸.۱:
  درصد کنکوری     = (درست − ۰.۳۳ × غلط) / کل × ۱۰۰
  درصد بدون غلط   = درست / کل × ۱۰۰
  total = درست + غلط + نزده
  اگر total = 0 → درصد None (تقسیم بر صفر)
  نتیجه کنکوری می‌تواند منفی باشد (نمایش واقعی با علامت منفی).
سیاست‌ها از ScoringPolicy خوانده می‌شوند — ضریب hard-code نمی‌شود.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScoringPolicy:
    """سیاست نمره‌دهی — ضریب نمره منفی (پیش‌فرض استاندارد: ۰.۳۳)."""

    wrong_penalty: float = 0.33

    def __post_init__(self) -> None:
        if not (0 <= self.wrong_penalty <= 1):
            raise ValueError("ضریب نمره منفی باید بین ۰ و ۱ باشد.")


@dataclass
class DifficultyBucket:
    """آمار یک سطح سختی."""

    total: int = 0
    correct: int = 0
    wrong: int = 0
    blank: int = 0
    percent_konkur: float | None = None
    percent_no_penalty: float | None = None

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "correct": self.correct,
            "wrong": self.wrong,
            "blank": self.blank,
            "percent_konkur": round(self.percent_konkur, 2) if self.percent_konkur is not None else None,
            "percent_no_penalty": round(self.percent_no_penalty, 2) if self.percent_no_penalty is not None else None,
        }


@dataclass
class ScoreResult:
    """نتیجه نمره‌دهی کامل."""

    total: int = 0
    correct: int = 0
    wrong: int = 0
    blank: int = 0
    percent_konkur: float | None = None
    percent_no_penalty: float | None = None
    difficulty_breakdown: dict[str, dict] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "correct": self.correct,
            "wrong": self.wrong,
            "blank": self.blank,
            "percent_konkur": round(self.percent_konkur, 2) if self.percent_konkur is not None else None,
            "percent_no_penalty": round(self.percent_no_penalty, 2) if self.percent_no_penalty is not None else None,
            "difficulty_breakdown": self.difficulty_breakdown,
        }


def konkur_percent(correct: int, wrong: int, total: int,
                   policy: ScoringPolicy | None = None) -> float | None:
    """درصد کنکوری با نمره منفی — فرمول استاندارد (AT-21).

    اگر total = 0 باشد None برمی‌گردد (تقسیم بر صفر — قانون ۸.۶).
    نتیجه ممکن است منفی باشد و همان‌طور برگردانده می‌شود.
    """
    if total <= 0:
        return None
    penalty = (policy or ScoringPolicy()).wrong_penalty
    return (correct - penalty * wrong) / total * 100


def no_penalty_percent(correct: int, total: int) -> float | None:
    """درصد بدون احتساب غلط."""
    if total <= 0:
        return None
    return correct / total * 100


def score_answers(
    answers: list[dict],
    question_difficulties: dict[str, str | None],
    policy: ScoringPolicy | None = None,
) -> ScoreResult:
    """نمره‌دهی مجموعه پاسخ‌ها + تحلیل بر اساس سطح سختی (AT-22).

    answers: [{"question_id": str, "result": "correct|wrong|blank"}]
    question_difficulties: نگاشت question_id → سطح سختی (سوال بدون سختی در تحلیل سختی نادیده گرفته می‌شود)
    """
    result = ScoreResult()
    buckets: dict[str, DifficultyBucket] = {
        "easy": DifficultyBucket(), "medium": DifficultyBucket(), "hard": DifficultyBucket(),
    }

    for answer in answers:
        outcome = answer["result"]
        result.total += 1
        if outcome == "correct":
            result.correct += 1
        elif outcome == "wrong":
            result.wrong += 1
        else:
            result.blank += 1
        difficulty = question_difficulties.get(answer["question_id"])
        if difficulty in buckets:  # سوال بدون سطح سختی نادیده گرفته می‌شود
            bucket = buckets[difficulty]
            bucket.total += 1
            if outcome == "correct":
                bucket.correct += 1
            elif outcome == "wrong":
                bucket.wrong += 1
            else:
                bucket.blank += 1

    result.percent_konkur = konkur_percent(result.correct, result.wrong, result.total, policy)
    result.percent_no_penalty = no_penalty_percent(result.correct, result.total)
    for difficulty, bucket in buckets.items():
        bucket.percent_konkur = konkur_percent(bucket.correct, bucket.wrong, bucket.total, policy)
        bucket.percent_no_penalty = no_penalty_percent(bucket.correct, bucket.total)
        result.difficulty_breakdown[difficulty] = bucket.as_dict()

    return result


@dataclass
class ExamPolicy:
    """سیاست آزمون — محدودیت‌های قابل تنظیم (محدودیت ۸.۷)."""

    max_questions: int = 200

    def __post_init__(self) -> None:
        if self.max_questions < 1:
            raise ValueError("حداکثر تعداد سوال آزمون باید حداقل ۱ باشد.")
