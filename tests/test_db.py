import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from db import connect, init_db


def count(path: str, table: Literal["habit_templates", "habits"]) -> int:
    """Return the row count for a supported application table."""
    count_queries = {
        "habit_templates": "SELECT COUNT(*) FROM habit_templates",
        "habits": "SELECT COUNT(*) FROM habits",
    }
    with closing(connect(path)) as conn:
        return int(conn.execute(count_queries[table]).fetchone()[0])


def test_first_boot_creates_schema_and_seeds(tmp_path: Path) -> None:
    path = str(tmp_path / "nested" / "habits.db")  # parent dir does not exist yet
    init_db(path)
    assert count(path, "habit_templates") > 0


def test_second_boot_does_not_duplicate_or_wipe(tmp_path: Path) -> None:
    path = str(tmp_path / "habits.db")
    init_db(path)
    with closing(connect(path)) as conn:
        conn.execute("INSERT INTO habits (name, cadence) VALUES ('keep me', 'daily')")
        conn.commit()
    seeded = count(path, "habit_templates")
    init_db(path)
    assert count(path, "habit_templates") == seeded
    assert count(path, "habits") == 1


def test_boot_adds_schedule_fields_to_existing_database(tmp_path: Path) -> None:
    path = tmp_path / "legacy.db"
    with closing(sqlite3.connect(path)) as conn:
        conn.execute(
            """
            CREATE TABLE habits (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                cadence TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (date('now'))
            )
            """
        )
        conn.execute("INSERT INTO habits (name, cadence) VALUES ('Old daily', 'daily')")
        conn.execute("INSERT INTO habits (name, cadence) VALUES ('Old weekly', 'weekly')")
        conn.commit()

    init_db(path)
    with closing(connect(path)) as conn:
        schedules = conn.execute(
            "SELECT name, days_of_week, time_of_day FROM habits ORDER BY id"
        ).fetchall()

    assert tuple(schedules[0]) == ("Old daily", "0,1,2,3,4,5,6", "09:00")
    assert tuple(schedules[1]) == ("Old weekly", "0", "09:00")
