"""Pure streak logic for the habits domain (no DB, easy to unit test)."""

from datetime import date, timedelta


def current_daily_streak(checkin_dates: list[date], today: date) -> int:
    """Count consecutive days ending today or yesterday."""
    days = set(checkin_dates)
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _previous_iso_week(anchor_date: date) -> tuple[int, int]:
    """Return the ISO year and week immediately before the given date's week."""
    return (anchor_date - timedelta(days=7)).isocalendar()[:2]


def current_weekly_streak(checkin_dates: list[date], today: date) -> int:
    """Count consecutive ISO weeks with check-ins, allowing the current week to be incomplete."""
    if not checkin_dates:
        return 0

    checked_weeks = {d.isocalendar()[:2] for d in checkin_dates}
    cursor = today.isocalendar()[:2]

    if cursor not in checked_weeks:
        cursor = _previous_iso_week(today)

    streak = 0
    while cursor in checked_weeks:
        streak += 1
        cursor = _previous_iso_week(date.fromisocalendar(cursor[0], cursor[1], 1))

    return streak
