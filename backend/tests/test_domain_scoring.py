"""تست‌های واحد دامنه نمره‌دهی — حداقل ۱۰ سناریو مختلف (معیار AT-21)."""
from __future__ import annotations

import pytest

from app.modules.exam.domain import ScoringPolicy, konkur_percent, no_penalty_percent, score_answers


class TestKonkurPercent:
    """فرمول: (درست − ۰.۳۳ × غلط) / کل × ۱۰۰"""

    def test_scenario_1_basic(self):
        # 20 درست، 10 غلط، 10 نزده → (20 - 3.3)/40*100 = 41.75
        assert konkur_percent(20, 10, 40) == pytest.approx(41.75)

    def test_scenario_2_all_correct(self):
        assert konkur_percent(30, 0, 30) == pytest.approx(100.0)

    def test_scenario_3_all_wrong(self):
        # (0 - 0.33*30)/30*100 = -33
        assert konkur_percent(0, 30, 30) == pytest.approx(-33.0)

    def test_scenario_4_all_blank(self):
        assert konkur_percent(0, 0, 20) == pytest.approx(0.0)

    def test_scenario_5_zero_total_returns_none(self):
        # قانون ۸.۶: تقسیم بر صفر → None
        assert konkur_percent(0, 0, 0) is None

    def test_scenario_6_negative_result_kept(self):
        # نتیجه منفی با علامت منفی نمایش داده می‌شود (قانون ۸.۱)
        assert konkur_percent(1, 10, 11) < 0

    def test_scenario_7_custom_penalty(self):
        policy = ScoringPolicy(wrong_penalty=0.25)
        # (10 - 0.25*10)/20*100 = 37.5
        assert konkur_percent(10, 10, 20, policy) == pytest.approx(37.5)

    def test_scenario_8_zero_penalty(self):
        policy = ScoringPolicy(wrong_penalty=0.0)
        assert konkur_percent(10, 10, 20, policy) == pytest.approx(50.0)

    def test_scenario_9_mixed(self):
        # (45 - 0.33*15)/100*100 = 40.05
        assert konkur_percent(45, 15, 100) == pytest.approx(40.05)

    def test_scenario_10_single_question(self):
        assert konkur_percent(1, 0, 1) == pytest.approx(100.0)
        assert konkur_percent(0, 1, 1) == pytest.approx(-33.0)

    def test_scenario_11_typical_konkur(self):
        # سناریوی واقعی: 100 سوال، 60 درست، 25 غلط، 15 نزده
        # (60 - 8.25)/100*100 = 51.75
        assert konkur_percent(60, 25, 100) == pytest.approx(51.75)


class TestNoPenaltyPercent:
    def test_basic(self):
        assert no_penalty_percent(15, 20) == pytest.approx(75.0)

    def test_zero_total(self):
        assert no_penalty_percent(0, 0) is None

    def test_all_correct(self):
        assert no_penalty_percent(50, 50) == pytest.approx(100.0)


class TestScoreAnswers:
    def _answers(self, results: list[str]) -> list[dict]:
        return [{"question_id": f"q{i}", "result": r} for i, r in enumerate(results)]

    def test_full_scoring(self):
        answers = self._answers(["correct"] * 10 + ["wrong"] * 5 + ["blank"] * 5)
        difficulties = {f"q{i}": ["easy", "medium", "hard"][i % 3] for i in range(20)}
        result = score_answers(answers, difficulties)
        assert result.total == 20
        assert result.correct == 10
        assert result.wrong == 5
        assert result.blank == 5
        assert result.percent_konkur == pytest.approx((10 - 0.33 * 5) / 20 * 100)
        assert result.percent_no_penalty == pytest.approx(50.0)

    def test_difficulty_breakdown(self):
        # AT-22 — تحلیل سختی
        answers = self._answers(["correct", "wrong", "correct", "blank", "hard_correct"])
        answers[4]["result"] = "correct"
        difficulties = {
            "q0": "easy", "q1": "easy", "q2": "medium", "q3": "hard", "q4": "hard",
        }
        result = score_answers(answers, difficulties)
        assert result.difficulty_breakdown["easy"]["total"] == 2
        assert result.difficulty_breakdown["easy"]["correct"] == 1
        assert result.difficulty_breakdown["easy"]["wrong"] == 1
        assert result.difficulty_breakdown["medium"]["total"] == 1
        assert result.difficulty_breakdown["hard"]["correct"] == 1

    def test_questions_without_difficulty_ignored(self):
        # قانون ۸.۶: سوال بدون سطح سختی در تحلیل سختی نادیده گرفته می‌شود
        answers = self._answers(["correct", "wrong"])
        difficulties = {"q0": None, "q1": None}
        result = score_answers(answers, difficulties)
        assert result.total == 2
        assert sum(b["total"] for b in result.difficulty_breakdown.values()) == 0

    def test_empty_answers(self):
        result = score_answers([], {})
        assert result.total == 0
        assert result.percent_konkur is None

    def test_invalid_policy_rejected(self):
        with pytest.raises(ValueError):
            ScoringPolicy(wrong_penalty=2.0)
