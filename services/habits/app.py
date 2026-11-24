"""Habits HTTP service."""

import os
import time
from datetime import date, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pymssql
from flask import Flask, Response, g, jsonify, request
from schedule import due_reminders, parse_schedule


def parse_database_url(database_url: str) -> dict[str, object]:
    """Parse the service database URL into pymssql connection settings."""
    parsed = urlparse(database_url)
    if parsed.scheme not in ("mssql", "sqlserver"):
        raise RuntimeError("DATABASE_URL must use mssql://")
    query = parse_qs(parsed.query)
    return {
        "server": parsed.hostname,
        "port": parsed.port or 1433,
        "user": parsed.username,
        "password": parsed.password,
        "database": parsed.path.lstrip("/"),
        "login_timeout": int(query.get("login_timeout", ["5"])[0]),
    }


def connect_database() -> pymssql.Connection:
    """Open a SQL Server connection using DATABASE_URL."""
    settings = parse_database_url(os.environ["DATABASE_URL"])
    return pymssql.connect(**settings)


def get_database() -> pymssql.Connection:
    """Get the request database connection."""
    if "database" not in g:
        g.database = connect_database()
    return g.database


def close_database(_error: BaseException | None = None) -> None:
    """Close the request database connection."""
    database = g.pop("database", None)
    if database is not None:
        database.close()


def run_migrations() -> None:
    """Apply numbered SQL migrations once and in order."""
    database = connect_database()
    cursor = database.cursor()
    cursor.execute(
        "DECLARE @result INT; EXEC @result = sp_getapplock "
        "@Resource = 'habit-migrations', @LockMode = 'Exclusive', "
        "@LockOwner = 'Session', @LockTimeout = 60000;"
    )
    try:
        cursor.execute(
            """
            IF OBJECT_ID(N'dbo.schema_migrations', N'U') IS NULL
            BEGIN
                CREATE TABLE schema_migrations (
                    version NVARCHAR(20) PRIMARY KEY,
                    applied_at DATETIME2 NOT NULL
                );
            END
            """
        )
        database.commit()

        cursor.execute("SELECT version FROM schema_migrations")
        applied = {row[0] for row in cursor.fetchall()}
        migration_directory = Path(__file__).parent / "migrations"
        for migration_path in sorted(migration_directory.glob("*.sql")):
            version = migration_path.stem
            if version in applied:
                continue
            statements = migration_path.read_text(encoding="utf-8").split(";")
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
            cursor.execute(
                "INSERT INTO schema_migrations (version, applied_at) "
                "VALUES (%s, SYSUTCDATETIME())",
                (version,),
            )
            database.commit()
    finally:
        cursor.execute(
            "EXEC sp_releaseapplock "
            "@Resource = 'habit-migrations', @LockOwner = 'Session';"
        )
        database.commit()
        database.close()


def retry_migrations() -> None:
    """Retry startup migrations while Azure SQL is resuming."""
    for attempt in range(12):
        try:
            run_migrations()
            return
        except pymssql.Error:
            if attempt == 11:
                raise
            time.sleep(5)


def create_app() -> Flask:
    """Create and configure the habits Flask app."""
    app = Flask(__name__)
    app.teardown_appcontext(close_database)

    @app.before_request
    def start_timer() -> None:
        g.request_started = time.perf_counter()

    @app.after_request
    def finish_request(response: Response) -> Response:
        elapsed_ms = int((time.perf_counter() - g.request_started) * 1000)
        print(
            f"{request.method} {request.path} {response.status_code} {elapsed_ms}ms",
            flush=True,
        )
        origin = os.environ.get("UI_ORIGIN", "")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,DELETE,OPTIONS"
        return response

    @app.get("/health")
    def health() -> tuple[Response, int]:
        """Report database read/write health for this service only."""
        try:
            database = get_database()
            cursor = database.cursor(as_dict=True)
            cursor.execute("SELECT 1 AS ok")
            cursor.fetchone()
            cursor.execute(
                "INSERT INTO health_probe (checked_at) "
                "VALUES (CONVERT(NVARCHAR(30), SYSUTCDATETIME(), 126))"
            )
            database.rollback()
            return jsonify(status="ok", db="ok", version=os.environ.get("GIT_SHA", "unknown")), 200
        except pymssql.Error:
            return jsonify(
                status="unhealthy",
                db="unavailable",
                version=os.environ.get("GIT_SHA", "unknown"),
            ), 503

    @app.route("/habits", methods=["GET", "OPTIONS"])
    def list_habits() -> Response:
        """List habits."""
        cursor = get_database().cursor(as_dict=True)
        cursor.execute(
            "SELECT id, name, cadence, days_of_week, time_of_day, "
            "alert_type, alert_offset_minutes FROM habits ORDER BY id"
        )
        result = []
        for row in cursor.fetchall():
            row["days_of_week"] = [int(day) for day in row["days_of_week"].split(",")]
            result.append(row)
        return jsonify(result)

    @app.post("/habits")
    def create_habit() -> tuple[Response, int]:
        """Create a habit."""
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify(error="request body must be a JSON object"), 400
        schedule = parse_schedule(data)
        name = data.get("name")
        if not isinstance(name, str) or not name.strip() or schedule is None:
            return jsonify(error="invalid name or schedule"), 400
        cadence = "daily" if len(schedule["days_of_week"]) == 7 else "weekly"
        database = get_database()
        cursor = database.cursor(as_dict=True)
        cursor.execute(
            """
            INSERT INTO habits
                (name, cadence, days_of_week, time_of_day, alert_type,
                 alert_offset_minutes, created_at)
            OUTPUT INSERTED.id
            VALUES (%s, %s, %s, %s, %s, %s,
                    CONVERT(NVARCHAR(10), SYSUTCDATETIME(), 23))
            """,
            (
                name.strip(),
                cadence,
                ",".join(str(day) for day in schedule["days_of_week"]),
                schedule["time_of_day"],
                schedule["alert_type"],
                schedule["alert_offset_minutes"],
            ),
        )
        row = cursor.fetchone()
        database.commit()
        return jsonify(id=row["id"], name=name.strip(), cadence=cadence, **schedule), 201

    @app.delete("/habits/<int:habit_id>")
    def delete_habit(habit_id: int) -> tuple[Response, int]:
        """Delete a habit."""
        database = get_database()
        cursor = database.cursor()
        cursor.execute("DELETE FROM habits WHERE id = %s", (habit_id,))
        deleted = cursor.rowcount
        database.commit()
        if deleted == 0:
            return jsonify(error="habit not found"), 404
        return "", 204

    @app.post("/habits/<int:habit_id>/checkins")
    def check_in(habit_id: int) -> tuple[Response, int]:
        """Record one check-in for a habit."""
        data = request.get_json(silent=True)
        if data is not None and not isinstance(data, dict):
            return jsonify(error="request body must be a JSON object"), 400
        checked_on = (data or {}).get("date", date.today().isoformat())
        try:
            parsed = date.fromisoformat(str(checked_on))
        except ValueError:
            return jsonify(error="date must be YYYY-MM-DD"), 400
        if parsed.isoformat() != str(checked_on):
            return jsonify(error="date must be YYYY-MM-DD"), 400
        database = get_database()
        cursor = database.cursor(as_dict=True)
        cursor.execute("SELECT id FROM habits WHERE id = %s", (habit_id,))
        if cursor.fetchone() is None:
            return jsonify(error="habit not found"), 404
        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM checkins WHERE habit_id = %s AND checked_on = %s) "
            "INSERT INTO checkins (habit_id, checked_on) VALUES (%s, %s)",
            (habit_id, checked_on, habit_id, checked_on),
        )
        database.commit()
        return jsonify(habit_id=habit_id, date=checked_on), 201

    @app.get("/habits/templates")
    def templates() -> Response:
        """List seeded habit templates."""
        cursor = get_database().cursor(as_dict=True)
        cursor.execute("SELECT id, name, cadence FROM habit_templates ORDER BY id")
        return jsonify(cursor.fetchall())

    @app.post("/habits/from-template/<int:template_id>")
    def from_template(template_id: int) -> tuple[Response, int]:
        """Create a habit from a template."""
        cursor = get_database().cursor(as_dict=True)
        cursor.execute(
            "SELECT id, name, cadence FROM habit_templates WHERE id = %s",
            (template_id,),
        )
        template = cursor.fetchone()
        if template is None:
            return jsonify(error="template not found"), 404
        data = {"name": template["name"], "cadence": template["cadence"]}
        schedule = parse_schedule(data)
        if schedule is None:
            return jsonify(error="invalid template"), 500
        cursor.execute(
            """
            INSERT INTO habits
                (name, cadence, days_of_week, time_of_day, alert_type,
                 alert_offset_minutes, created_at)
            OUTPUT INSERTED.id
            VALUES (%s, %s, %s, %s, %s, %s,
                    CONVERT(NVARCHAR(10), SYSUTCDATETIME(), 23))
            """,
            (
                template["name"],
                template["cadence"],
                ",".join(str(day) for day in schedule["days_of_week"]),
                schedule["time_of_day"],
                schedule["alert_type"],
                schedule["alert_offset_minutes"],
            ),
        )
        row = cursor.fetchone()
        get_database().commit()
        return jsonify(id=row["id"], name=template["name"], cadence=template["cadence"]), 201

    @app.get("/habits/<int:habit_id>/public")
    def public_summary(habit_id: int) -> tuple[Response, int]:
        """Return the minimal seam payload for insights."""
        cursor = get_database().cursor(as_dict=True)
        cursor.execute(
            "SELECT id, days_of_week FROM habits WHERE id = %s",
            (habit_id,),
        )
        habit = cursor.fetchone()
        if habit is None:
            return jsonify(error="habit not found"), 404
        days = [int(day) for day in habit["days_of_week"].split(",")]
        cursor.execute(
            "SELECT checked_on FROM checkins WHERE habit_id = %s ORDER BY checked_on",
            (habit_id,),
        )
        checkins = [row["checked_on"] for row in cursor.fetchall()]
        checked_dates = [date.fromisoformat(value) for value in checkins]
        today = date.today()
        from schedule import current_scheduled_streak

        streak = current_scheduled_streak(checked_dates, days, today)
        return jsonify(
            habit_id=habit_id,
            exists=True,
            scheduled_weekdays=days,
            checkin_dates=checkins,
            streak=streak,
        ), 200

    @app.get("/habits/reminders")
    def reminders() -> Response:
        """Return due reminders for the open UI."""
        cursor = get_database().cursor(as_dict=True)
        cursor.execute(
            "SELECT id, name, days_of_week, time_of_day, " "alert_offset_minutes FROM habits"
        )
        habits = []
        for habit in cursor.fetchall():
            habit["days_of_week"] = [int(day) for day in habit["days_of_week"].split(",")]
            cursor.execute(
                "SELECT checked_on FROM checkins WHERE habit_id = %s",
                (habit["id"],),
            )
            habit["checkin_dates"] = [row["checked_on"] for row in cursor.fetchall()]
            habits.append(habit)
        return jsonify(due_reminders(habits, datetime.now()))

    return app


app = create_app()
