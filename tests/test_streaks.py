from datetime import date, timedelta

from habits.streaks import current_daily_streak

TODAY = date(2026, 10, 9)


def days_ago(*offsets):
    return [TODAY - timedelta(days=n) for n in offsets]


def test_no_checkins_is_zero():
    assert current_daily_streak([], TODAY) == 0


def test_consecutive_days_including_today():
    assert current_daily_streak(days_ago(0, 1, 2), TODAY) == 3


def test_streak_alive_if_last_checkin_was_yesterday():
    assert current_daily_streak(days_ago(1, 2), TODAY) == 2


def test_gap_breaks_streak():
    assert current_daily_streak(days_ago(0, 1, 3, 4), TODAY) == 2


def test_stale_checkin_is_zero():
    assert current_daily_streak(days_ago(2, 3), TODAY) == 0
