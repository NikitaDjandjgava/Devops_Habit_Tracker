-- Habits domain: owns habits and check-ins.
CREATE TABLE IF NOT EXISTS habits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    cadence    TEXT NOT NULL CHECK (cadence IN ('daily', 'weekly')),
    created_at TEXT NOT NULL DEFAULT (date('now'))
);

CREATE TABLE IF NOT EXISTS checkins (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id   INTEGER NOT NULL REFERENCES habits(id) ON DELETE CASCADE,
    checked_on TEXT NOT NULL,                       -- ISO date YYYY-MM-DD
    UNIQUE (habit_id, checked_on)                   -- one check-in per habit per day
);

-- Reference data, loaded from seed.json on first boot.
CREATE TABLE IF NOT EXISTS habit_templates (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL UNIQUE,
    cadence TEXT NOT NULL CHECK (cadence IN ('daily', 'weekly'))
);

-- Insights domain: owns milestones.
-- habit_id deliberately has NO foreign key: this is the seam. In Assignment 2
-- this table moves to another service, so it must not depend on habits' tables.
CREATE TABLE IF NOT EXISTS milestones (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    habit_id    INTEGER NOT NULL,
    kind        TEXT NOT NULL,                      -- e.g. 'streak_7'
    achieved_on TEXT NOT NULL,
    UNIQUE (habit_id, kind)
);
