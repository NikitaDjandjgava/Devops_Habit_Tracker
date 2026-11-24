CREATE TABLE milestones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    habit_id INT NOT NULL,
    kind NVARCHAR(50) NOT NULL,
    achieved_on NVARCHAR(10) NOT NULL,
    CONSTRAINT uq_habit_milestone UNIQUE (habit_id, kind)
);

CREATE TABLE health_probe (
    id INT IDENTITY(1,1) PRIMARY KEY,
    checked_at NVARCHAR(30) NOT NULL
);
