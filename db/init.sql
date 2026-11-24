IF DB_ID(N'habits_db') IS NULL
BEGIN
    CREATE DATABASE habits_db;
END;
GO

IF DB_ID(N'insights_db') IS NULL
BEGIN
    CREATE DATABASE insights_db;
END;
GO

USE master;
IF SUSER_ID(N'habits_login') IS NULL
BEGIN
    CREATE LOGIN habits_login WITH PASSWORD = '$(HABITS_DB_PASSWORD)';
END;
IF SUSER_ID(N'insights_login') IS NULL
BEGIN
    CREATE LOGIN insights_login WITH PASSWORD = '$(INSIGHTS_DB_PASSWORD)';
END;
GO

USE habits_db;
IF DATABASE_PRINCIPAL_ID(N'habits_login') IS NULL
BEGIN
    CREATE USER habits_login FOR LOGIN habits_login;
END;
EXEC sp_addrolemember N'db_owner', N'habits_login';
GO

USE insights_db;
IF DATABASE_PRINCIPAL_ID(N'insights_login') IS NULL
BEGIN
    CREATE USER insights_login FOR LOGIN insights_login;
END;
EXEC sp_addrolemember N'db_owner', N'insights_login';
GO
