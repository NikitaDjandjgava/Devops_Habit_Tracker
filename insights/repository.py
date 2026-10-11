"""SQLite access for the insights domain."""

from insights.stats import milestone_kinds


def list_milestones(db, habit_id):
    rows = db.execute(
        "SELECT id, habit_id, kind, achieved_on FROM milestones WHERE habit_id = ? ORDER BY achieved_on, kind",
        (habit_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def record_milestones(db, habit_id, achieved_on, streak_value):
    for kind in milestone_kinds(streak_value):
        db.execute(
            "INSERT OR IGNORE INTO milestones (habit_id, kind, achieved_on) VALUES (?, ?, ?)",
            (habit_id, kind, achieved_on),
        )
    db.commit()
    return list_milestones(db, habit_id)
