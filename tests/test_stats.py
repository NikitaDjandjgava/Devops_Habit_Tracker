from datetime import date, datetime

import pytest

from insights.stats import best_weekday, completion_rate, milestone_kinds, scheduled_day_count


def test_completion_rate() -> None:
    assert completion_rate(3, 7) == pytest.approx(3 / 7)


def test_rate_is_capped_at_one() -> None:
    assert completion_rate(10, 7) == 1.0


def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError):
        completion_rate(1, 0)


def test_scheduled_day_count_only_counts_selected_weekdays() -> None:
    monday = date(2026, 10, 5)
    sunday = date(2026, 10, 11)
    assert scheduled_day_count([0, 2, 4], monday, sunday) == 3
    assert scheduled_day_count([0], monday, sunday) == 1


def test_best_weekday_and_milestones() -> None:
    checkins = [date(2026, 10, 5), date(2026, 10, 12), date(2026, 10, 12)]
    assert best_weekday(checkins) == "Monday"
    assert milestone_kinds(31) == ["streak_7", "streak_30"]


def test_best_weekday_supports_datetime_ties_and_milestone_ranges() -> None:
    checkins = [
        datetime(2026, 10, 5, 8, 30),
        datetime(2026, 10, 5, 18, 30),
        datetime(2026, 10, 7, 12, 0),
    ]
    assert best_weekday(checkins) == "Monday"
    assert milestone_kinds(90) == ["streak_7", "streak_30", "streak_90"]


def test_best_weekday_supports_iso_strings_and_empty_input() -> None:
    assert best_weekday(["2026-10-09"]) == "Friday"
    assert best_weekday([]) is None
