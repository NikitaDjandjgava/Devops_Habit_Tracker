"""All SQL for the habits domain lives here."""


def create_habit(db, name, cadence):
    cur = db.execute("INSERT INTO habits (name, cadence) VALUES (?, ?)", (name, cadence))
    db.commit()
    return cur.lastrowid


def list_habits(db):
    return [dict(r) for r in db.execute("SELECT id, name, cadence FROM habits ORDER BY id")]


def list_templates(db):
    return [dict(r) for r in db.execute("SELECT id, name, cadence FROM habit_templates ORDER BY id")]


def get_habit(db, habit_id):
    row = db.execute("SELECT id, name, cadence FROM habits WHERE id = ?", (habit_id,)).fetchone()
    return dict(row) if row else None


def get_template(db, template_id):
    row = db.execute(
        "SELECT id, name, cadence FROM habit_templates WHERE id = ?",
        (template_id,),
    ).fetchone()
    return dict(row) if row else None


def add_checkin(db, habit_id, checked_on):
    """Idempotent: a second check-in on the same day is ignored (UNIQUE constraint)."""
    db.execute(
        "INSERT OR IGNORE INTO checkins (habit_id, checked_on) VALUES (?, ?)",
        (habit_id, checked_on),
    )
    db.commit()


def get_checkin_dates(db, habit_id, start=None, end=None):
    """Return a sorted list of ISO date strings, optionally bounded (inclusive)."""
    sql = "SELECT checked_on FROM checkins WHERE habit_id = ?"
    params = [habit_id]
    if start:
        sql += " AND checked_on >= ?"
        params.append(start)
    if end:
        sql += " AND checked_on <= ?"
        params.append(end)
    return [r[0] for r in db.execute(sql + " ORDER BY checked_on", params)]
