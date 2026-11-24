ALTER TABLE habits ADD color NVARCHAR(20) NULL;

UPDATE habits
SET color = CASE (id % 8)
    WHEN 0 THEN N'blue'
    WHEN 1 THEN N'green'
    WHEN 2 THEN N'teal'
    WHEN 3 THEN N'purple'
    WHEN 4 THEN N'orange'
    WHEN 5 THEN N'red'
    WHEN 6 THEN N'yellow'
    ELSE N'gray'
END;

ALTER TABLE habits ALTER COLUMN color NVARCHAR(20) NOT NULL;
