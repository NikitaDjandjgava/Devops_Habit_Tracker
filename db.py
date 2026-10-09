"""SQLite access: connection handling, schema creation, idempotent seeding."""
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from flask import current_app, g

BASE_DIR = Path(__file__).parent


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path):
    """Create missing tables and seed empty reference tables.

    Safe to call on every boot: it only creates what is missing
    (CREATE TABLE IF NOT EXISTS) and never drops or overwrites data.
    """
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(db_path)) as conn:
        conn.executescript((BASE_DIR / "schema.sql").read_text())
        _seed_habit_templates(conn)
        conn.commit()


def _seed_habit_templates(conn):
    count = conn.execute("SELECT COUNT(*) FROM habit_templates").fetchone()[0]
    if count > 0:  # idempotency guard: only seed an empty table
        return
    seed = json.loads((BASE_DIR / "seed.json").read_text())
    conn.executemany(
        "INSERT INTO habit_templates (name, cadence) VALUES (:name, :cadence)",
        seed["habit_templates"],
    )


def get_db():
    """One connection per request, stored on flask.g."""
    if "db" not in g:
        g.db = connect(current_app.config["DB_PATH"])
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
