from datetime import date, timedelta

from habits.streaks import current_daily_streak, current_weekly_streak
from insights.stats import best_weekday, milestone_kinds

TODAY = date(2026, 10, 9)


def days_ago(*offsets: int) -> list[date]:
    return [TODAY - timedelta(days=n) for n in offsets]


def test_no_checkins_is_zero() -> None:
    assert current_daily_streak([], TODAY) == 0


def test_consecutive_days_including_today() -> None:
    assert current_daily_streak(days_ago(0, 1, 2), TODAY) == 3


def test_streak_alive_if_last_checkin_was_yesterday() -> None:
    assert current_daily_streak(days_ago(1, 2), TODAY) == 2


def test_gap_breaks_streak() -> None:
    assert current_daily_streak(days_ago(0, 1, 3, 4), TODAY) == 2


def test_stale_checkin_is_zero() -> None:
    assert current_daily_streak(days_ago(2, 3), TODAY) == 0


def test_weekly_streak_counts_consecutive_weeks() -> None:
    dates = [
        date(2026, 10, 2),
        date(2026, 9, 25),
        date(2026, 9, 18),
    ]
    assert current_weekly_streak(dates, TODAY) == 3


def test_best_weekday_uses_the_most_common_day() -> None:
    dates = [
        date(2026, 10, 1),
        date(2026, 10, 7),
        date(2026, 10, 7),
        date(2026, 10, 8),
    ]
    assert best_weekday(dates) == "Wednesday"


def test_best_weekday_accepts_iso_dates_and_returns_none_when_empty() -> None:
    assert best_weekday(["2026-10-09"]) == "Friday"
    assert best_weekday([]) is None


def test_milestone_kinds_are_derived_from_streak_length() -> None:
    assert milestone_kinds(31) == ["streak_7", "streak_30"]
