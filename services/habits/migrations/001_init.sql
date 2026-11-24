CREATE TABLE habits (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL,
    cadence NVARCHAR(20) NOT NULL,
    days_of_week NVARCHAR(20) NOT NULL,
    time_of_day NVARCHAR(5) NOT NULL,
    alert_type NVARCHAR(20) NOT NULL,
    alert_offset_minutes INT NOT NULL,
    created_at NVARCHAR(10) NOT NULL
);

CREATE TABLE checkins (
    id INT IDENTITY(1,1) PRIMARY KEY,
    habit_id INT NOT NULL,
    checked_on NVARCHAR(10) NOT NULL,
    CONSTRAINT fk_checkins_habit FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE,
    CONSTRAINT uq_habit_checkin UNIQUE (habit_id, checked_on)
);

CREATE TABLE habit_templates (
    id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(200) NOT NULL UNIQUE,
    cadence NVARCHAR(20) NOT NULL
);

CREATE TABLE health_probe (
    id INT IDENTITY(1,1) PRIMARY KEY,
    checked_at NVARCHAR(30) NOT NULL
);

INSERT INTO habit_templates (name, cadence)
SELECT name, cadence
FROM (VALUES
    (N'Drink water', N'daily'),
    (N'Exercise', N'daily'),
    (N'Read', N'daily'),
    (N'Stretch', N'daily'),
    (N'Plan week', N'weekly')
) AS seed(name, cadence)
WHERE NOT EXISTS (
    SELECT 1 FROM habit_templates WHERE habit_templates.name = seed.name
);
