from contextlib import closing

from db import connect, init_db


def count(path, table):
    with closing(connect(path)) as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_first_boot_creates_schema_and_seeds(tmp_path):
    path = str(tmp_path / "nested" / "habits.db")  # parent dir does not exist yet
    init_db(path)
    assert count(path, "habit_templates") > 0


def test_second_boot_does_not_duplicate_or_wipe(tmp_path):
    path = str(tmp_path / "habits.db")
    init_db(path)
    with closing(connect(path)) as conn:
        conn.execute("INSERT INTO habits (name, cadence) VALUES ('keep me', 'daily')")
        conn.commit()
    seeded = count(path, "habit_templates")
    init_db(path)
    assert count(path, "habit_templates") == seeded
    assert count(path, "habits") == 1
