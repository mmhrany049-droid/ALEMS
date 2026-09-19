"""منطق دامنه مرور (Review Management) — قوانین صف مرور و تکرار با فاصله.

همه قوانین کسب‌وکار مرور اینجاست: بدون دیتابیس، بدون فریم‌ورک، کاملاً قابل‌تست.
سیاست‌ها (اولویت‌ها، چرخه روزها، ورود نزده‌ها) قابل تنظیم از Settings هستند.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

from app.shared.exceptions import ValidationError

REVIEW_REASONS = ("wrong", "blank", "mark_important", "mark_hard", "mark_review")

# علت‌های مرتبط با تیک‌ها
MARK_TO_REASON = {
    "important": "mark_important",
    "hard": "mark_hard",
    "review": "mark_review",
}


@dataclass
class ReviewPolicy:
    """سیاست صف مرور — مقادیر پیش‌فرض قابل بازنویسی از تنظیمات برنامه."""

    # اولویت پایه هر علت (عدد بزرگ‌تر = مهم‌تر)
    priority_by_reason: dict[str, int] = field(default_factory=lambda: {
        "wrong": 5,
        "mark_important": 4,
        "mark_hard": 3,
        "mark_review": 3,
        "blank": 2,
    })
    # آیا نزده‌ها وارد صف شوند؟ (تنظیم کاربر — قانون ۸.۲ بند ۳)
    include_blank: bool = False
    # چرخه تکرار با فاصله (روز) — قانون ۸.۲ بند ۶: ۱ → ۳ → ۷ → ۱۴
    intervals_days: tuple[int, ...] = (1, 3, 7, 14)

    def to_settings(self) -> dict:
        return {
            "priority_by_reason": self.priority_by_reason,
            "include_blank": self.include_blank,
            "intervals_days": list(self.intervals_days),
        }

    @classmethod
    def from_settings(cls, data: dict | None) -> "ReviewPolicy":
        policy = cls()
        if not data:
            return policy
        if "priority_by_reason" in data and isinstance(data["priority_by_reason"], dict):
            policy.priority_by_reason = {str(k): int(v) for k, v in data["priority_by_reason"].items()}
        if "include_blank" in data:
            policy.include_blank = bool(data["include_blank"])
        if "intervals_days" in data and isinstance(data["intervals_days"], list):
            intervals = tuple(int(x) for x in data["intervals_days"] if int(x) > 0)
            if intervals:
                policy.intervals_days = intervals
        return policy

    def priority_for(self, reasons: list[str]) -> int:
        """اولویت آیتم = بیشترین اولویت بین علت‌ها."""
        return max((self.priority_by_reason.get(r, 1) for r in reasons), default=1)

    def next_review_date(self, review_count: int, from_date: dt.date | None = None) -> dt.date:
        """تاریخ پیشنهادی مرور بعدی بر اساس چرخه ۱-۳-۷-۱۴.

        review_count = تعداد دفعات مرور انجام‌شده تاکنون (۰ یعنی هنوز مرور اول نشده).
        پس از آخرین چرخه، بزرگ‌ترین فاصله تکرار می‌شود.
        """
        base = from_date or dt.date.today()
        index = min(max(review_count, 0), len(self.intervals_days) - 1)
        return base + dt.timedelta(days=self.intervals_days[index])


@dataclass
class QueueEntryPlan:
    """برنامه ساخت یک آیتم صف مرور — خروجی محاسبه دامنه."""

    question_id: str
    reasons: list[str]
    priority: int
    scheduled_date: dt.date


def compute_queue_plans(
    *,
    wrong_question_ids: list[str],
    blank_question_ids: list[str],
    marked_question_ids: dict[str, list[str]],
    policy: ReviewPolicy,
    today: dt.date | None = None,
) -> dict[str, QueueEntryPlan]:
    """محاسبه صف مرور بر اساس قوانین ۸.۲ — خروجی: به ازای هر سوال یک طرح.

    ورودی‌ها:
      - wrong_question_ids: سوالاتی که آخرین نتیجه‌شان «غلط» است
      - blank_question_ids: سوالاتی که آخرین نتیجه‌شان «نزده» است
      - marked_question_ids: سوال به تیک‌های مرتبط با مرور (review/important/hard)

    قانون‌ها:
      ۱. غلط‌ها همیشه وارد صف می‌شوند.
      ۲. سوالات با تیک مرور/مهم/سخت وارد صف می‌شوند.
      ۳. نزده‌ها بسته به تنظیم کاربر (policy.include_blank).
    """
    today = today or dt.date.today()
    plans: dict[str, QueueEntryPlan] = {}

    def add_plan(question_id: str, reason: str) -> None:
        plan = plans.get(question_id)
        if plan is None:
            plans[question_id] = QueueEntryPlan(
                question_id=question_id, reasons=[reason],
                priority=policy.priority_for([reason]), scheduled_date=today,
            )
        else:
            if reason not in plan.reasons:
                plan.reasons.append(reason)
                plan.priority = policy.priority_for(plan.reasons)

    for qid in wrong_question_ids:
        add_plan(str(qid), "wrong")
    if policy.include_blank:
        for qid in blank_question_ids:
            add_plan(str(qid), "blank")
    for qid, marks in marked_question_ids.items():
        for mark in marks:
            reason = MARK_TO_REASON.get(mark)
            if reason:
                add_plan(str(qid), reason)

    return plans


def validate_error_type(error_type: str | None, result: str) -> str | None:
    """ثبت نوع اشتباه فقط برای نتیجه «غلط» مجاز است (قانون ۸.۳)."""
    from app.modules.activity.models import ERROR_TYPES

    if result == "wrong":
        if error_type is None:
            return "unknown"  # پیش‌فرض
        if error_type not in ERROR_TYPES:
            raise ValidationError(
                f"نوع اشتباه نامعتبر است: «{error_type}». مقادیر مجاز: {', '.join(ERROR_TYPES)}"
            )
        return error_type
    if error_type is not None:
        raise ValidationError("ثبت نوع اشتباه فقط برای سوالات غلط مجاز است.")
    return None
