"""Pure streak logic for the habits domain (no DB, easy to unit test)."""
from datetime import date, timedelta


def current_daily_streak(checkin_dates, today):
    """Count consecutive days ending today, or yesterday if not yet checked today.

    A streak is still alive if you checked in yesterday but haven't yet today.
    """
    days = set(checkin_dates)
    cursor = today if today in days else today - timedelta(days=1)
    streak = 0
    while cursor in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


# TODO: current_weekly_streak(checkin_dates, today) for cadence='weekly'
