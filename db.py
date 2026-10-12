"""SQLite access: connection handling, schema creation, idempotent seeding."""

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import current_app, g

BASE_DIR = Path(__file__).parent


def connect(db_path: str | Path) -> sqlite3.Connection:
    """Open SQLite with row access and foreign-key checks enabled."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str | Path) -> None:
    """Create missing tables and seed empty reference tables without replacing data."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(db_path)) as conn:
        conn.executescript((BASE_DIR / "schema.sql").read_text())
        _seed_habit_templates(conn)
        conn.commit()


def _seed_habit_templates(conn: sqlite3.Connection) -> None:
    """Insert bundled templates only when the template table is empty."""
    count = conn.execute("SELECT COUNT(*) FROM habit_templates").fetchone()[0]
    if count > 0:  # idempotency guard: only seed an empty table
        return
    seed = json.loads((BASE_DIR / "seed.json").read_text())
    conn.executemany(
        "INSERT INTO habit_templates (name, cadence) VALUES (:name, :cadence)",
        seed["habit_templates"],
    )


def get_db() -> sqlite3.Connection:
    """Get the current request's SQLite connection."""
    if "db" not in g:
        g.db = connect(current_app.config["DB_PATH"])
    return g.db


def close_db(_exc: BaseException | None = None) -> None:
    """Close and remove the current request's SQLite connection."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
