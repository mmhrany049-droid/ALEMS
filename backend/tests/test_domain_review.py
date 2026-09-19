"""تست‌های واحد دامنه مرور — قوانین صف مرور و چرخه تکرار (۸.۲)."""
from __future__ import annotations

import datetime as dt

from app.modules.activity.domain import ReviewPolicy, compute_queue_plans, validate_error_type


class TestQueuePlans:
    def test_wrong_enters_queue(self):
        plans = compute_queue_plans(
            wrong_question_ids=["q1"], blank_question_ids=[],
            marked_question_ids={}, policy=ReviewPolicy(),
        )
        assert "q1" in plans
        assert plans["q1"].reasons == ["wrong"]

    def test_marks_enter_queue(self):
        # تیک‌های review/important/hard وارد صف می‌شوند
        plans = compute_queue_plans(
            wrong_question_ids=[], blank_question_ids=[],
            marked_question_ids={"q2": ["important"], "q3": ["hard"], "q4": ["review"]},
            policy=ReviewPolicy(),
        )
        assert {"q2", "q3", "q4"} <= set(plans)

    def test_blank_optional(self):
        # نزده‌ها فقط با تنظیم کاربر وارد صف می‌شوند (قانون ۸.۲ بند ۳)
        kwargs = dict(wrong_question_ids=[], blank_question_ids=["q5"],
                      marked_question_ids={})
        plans = compute_queue_plans(**kwargs, policy=ReviewPolicy(include_blank=False))
        assert "q5" not in plans
        plans = compute_queue_plans(**kwargs, policy=ReviewPolicy(include_blank=True))
        assert "q5" in plans

    def test_multiple_reasons_priority_max(self):
        # سوال غلط + مهم → اولویت برابر max(5, 4) = 5
        plans = compute_queue_plans(
            wrong_question_ids=["q1"], blank_question_ids=[],
            marked_question_ids={"q1": ["important"]},
            policy=ReviewPolicy(),
        )
        assert set(plans["q1"].reasons) == {"wrong", "mark_important"}
        assert plans["q1"].priority == 5

    def test_priority_order_wrong_above_blank(self):
        plans = compute_queue_plans(
            wrong_question_ids=["q1"], blank_question_ids=["q2"],
            marked_question_ids={}, policy=ReviewPolicy(include_blank=True),
        )
        assert plans["q1"].priority > plans["q2"].priority


class TestSpacedRepetition:
    def test_cycle_1_3_7_14(self):
        # قانون ۸.۲ بند ۶: چرخه ۱ → ۳ → ۷ → ۱۴ روز
        policy = ReviewPolicy()
        today = dt.date(2026, 9, 19)  # شنبه
        assert policy.next_review_date(0, today) == today + dt.timedelta(days=1)
        assert policy.next_review_date(1, today) == today + dt.timedelta(days=3)
        assert policy.next_review_date(2, today) == today + dt.timedelta(days=7)
        assert policy.next_review_date(3, today) == today + dt.timedelta(days=14)

    def test_cycle_caps_at_last_interval(self):
        policy = ReviewPolicy()
        today = dt.date(2026, 9, 19)
        # بعد از چند مرور، بزرگ‌ترین فاصله تکرار می‌شود
        assert policy.next_review_date(10, today) == today + dt.timedelta(days=14)

    def test_custom_intervals(self):
        policy = ReviewPolicy.from_settings({"intervals_days": [2, 4]})
        today = dt.date(2026, 1, 1)
        assert policy.next_review_date(0, today) == today + dt.timedelta(days=2)
        assert policy.next_review_date(5, today) == today + dt.timedelta(days=4)

    def test_policy_from_settings_full(self):
        policy = ReviewPolicy.from_settings({
            "include_blank": True,
            "priority_by_reason": {"wrong": 10},
            "intervals_days": [1, 2, 3],
        })
        assert policy.include_blank is True
        assert policy.priority_by_reason["wrong"] == 10
        assert policy.intervals_days == (1, 2, 3)


class TestErrorTypeValidation:
    def test_error_type_only_for_wrong(self):
        # قانون ۸.۳: ثبت نوع اشتباه فقط برای «غلط» مجاز است
        assert validate_error_type("careless", "wrong") == "careless"
        assert validate_error_type(None, "wrong") == "unknown"

    def test_error_type_rejected_for_correct(self):
        import pytest

        from app.shared.exceptions import ValidationError

        with pytest.raises(ValidationError):
            validate_error_type("careless", "correct")

    def test_invalid_error_type(self):
        import pytest

        from app.shared.exceptions import ValidationError

        with pytest.raises(ValidationError):
            validate_error_type("nonsense", "wrong")
