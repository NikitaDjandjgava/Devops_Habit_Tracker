"""All SQL for the habits domain lives here."""

import sqlite3
from typing import Any


def create_habit(db: sqlite3.Connection, name: str, cadence: str) -> int:
    """Create a habit and return its generated identifier."""
    cur = db.execute("INSERT INTO habits (name, cadence) VALUES (?, ?)", (name, cadence))
    db.commit()
    if cur.lastrowid is None:
        raise RuntimeError("SQLite did not return an ID for the new habit")
    return cur.lastrowid


def list_habits(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return habits ordered by identifier."""
    return [dict(r) for r in db.execute("SELECT id, name, cadence FROM habits ORDER BY id")]


def list_templates(db: sqlite3.Connection) -> list[dict[str, Any]]:
    """Return available templates ordered by identifier."""
    return [
        dict(r) for r in db.execute("SELECT id, name, cadence FROM habit_templates ORDER BY id")
    ]


def get_habit(db: sqlite3.Connection, habit_id: int) -> dict[str, Any] | None:
    """Find a habit by identifier, returning None when it does not exist."""
    row = db.execute("SELECT id, name, cadence FROM habits WHERE id = ?", (habit_id,)).fetchone()
    return dict(row) if row else None


def get_template(db: sqlite3.Connection, template_id: int) -> dict[str, Any] | None:
    """Find a habit template by identifier, returning None when it does not exist."""
    row = db.execute(
        "SELECT id, name, cadence FROM habit_templates WHERE id = ?",
        (template_id,),
    ).fetchone()
    return dict(row) if row else None


def add_checkin(db: sqlite3.Connection, habit_id: int, checked_on: str) -> None:
    """Add a check-in and ignore duplicates for the same habit and date."""
    db.execute(
        "INSERT OR IGNORE INTO checkins (habit_id, checked_on) VALUES (?, ?)",
        (habit_id, checked_on),
    )
    db.commit()


def delete_checkin(db: sqlite3.Connection, habit_id: int, checked_on: str) -> None:
    """Remove one habit check-in on the specified date."""
    db.execute(
        "DELETE FROM checkins WHERE habit_id = ? AND checked_on = ?",
        (habit_id, checked_on),
    )
    db.commit()


def get_checkin_dates(
    db: sqlite3.Connection,
    habit_id: int,
    start: str | None = None,
    end: str | None = None,
) -> list[str]:
    """Return sorted ISO check-in dates, optionally bounded inclusively."""
    sql = "SELECT checked_on FROM checkins WHERE habit_id = ?"
    params: list[int | str] = [habit_id]
    if start:
        sql += " AND checked_on >= ?"
        params.append(start)
    if end:
        sql += " AND checked_on <= ?"
        params.append(end)
    return [r[0] for r in db.execute(sql + " ORDER BY checked_on", params)]
