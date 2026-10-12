"""SQLite access for the insights domain."""

import sqlite3
from typing import Any

from insights.stats import milestone_kinds


def list_milestones(db: sqlite3.Connection, habit_id: int) -> list[dict[str, Any]]:
    """Return recorded milestones for one habit ordered by date and kind."""
    rows = db.execute(
        "SELECT id, habit_id, kind, achieved_on FROM milestones "
        "WHERE habit_id = ? ORDER BY achieved_on, kind",
        (habit_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def record_milestones(
    db: sqlite3.Connection,
    habit_id: int,
    achieved_on: str,
    streak_value: int,
) -> list[dict[str, Any]]:
    """Persist newly achieved milestones and return all milestones for the habit."""
    for kind in milestone_kinds(streak_value):
        db.execute(
            "INSERT OR IGNORE INTO milestones (habit_id, kind, achieved_on) VALUES (?, ?, ?)",
            (habit_id, kind, achieved_on),
        )
    db.commit()
    return list_milestones(db, habit_id)
