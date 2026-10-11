"""THE SEAM. The only habits-domain functions other domains may import.

In Assignment 2 each function here becomes an HTTP endpoint on the habits
service. Insights must never import habits.repository or query habits tables.
"""
from datetime import date

from habits import repository
from habits.streaks import current_daily_streak, current_weekly_streak


def checkin_dates(db, habit_id, start=None, end=None):
    return repository.get_checkin_dates(db, habit_id, start, end)


def habit_exists(db, habit_id):
    return repository.get_habit(db, habit_id) is not None


def current_streak(db, habit_id, today):
    habit = repository.get_habit(db, habit_id)
    if habit is None:
        return 0

    dates = [date.fromisoformat(d) for d in repository.get_checkin_dates(db, habit_id)]
    if habit["cadence"] == "weekly":
        return current_weekly_streak(dates, today)
    return current_daily_streak(dates, today)
