"""THE SEAM. The only habits-domain functions other domains may import.

In Assignment 2 each function here becomes an HTTP endpoint on the habits
service. Insights must never import habits.repository or query habits tables.
"""

import sqlite3
from datetime import date

from habits import repository
from habits.schedule import current_scheduled_streak


def checkin_dates(
    db: sqlite3.Connection,
    habit_id: int,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """Return sorted ISO check-in dates through the habits public boundary."""
    return repository.get_checkin_dates(db, habit_id, start, end)


def habit_exists(db: sqlite3.Connection, habit_id: int) -> bool:
    """Check whether a habit exists without exposing habits storage details."""
    return repository.get_habit(db, habit_id) is not None


def scheduled_weekdays(db: sqlite3.Connection, habit_id: int) -> list[int]:
    """Return the habit's scheduled weekday numbers, Monday as 0."""
    habit = repository.get_habit(db, habit_id)
    if habit is None:
        return []
    return habit["days_of_week"]


def current_streak(db: sqlite3.Connection, habit_id: int, today: date) -> int:
    """Calculate a habit's active streak according to its cadence."""
    habit = repository.get_habit(db, habit_id)
    if habit is None:
        return 0

    dates = [date.fromisoformat(d) for d in repository.get_checkin_dates(db, habit_id)]
    return current_scheduled_streak(dates, habit["days_of_week"], today)
