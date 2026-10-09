"""THE SEAM. The only habits-domain functions other domains may import.

In Assignment 2 each function here becomes an HTTP endpoint on the habits
service. Insights must never import habits.repository or query habits tables.
"""
from habits import repository


def checkin_dates(db, habit_id, start=None, end=None):
    return repository.get_checkin_dates(db, habit_id, start, end)
