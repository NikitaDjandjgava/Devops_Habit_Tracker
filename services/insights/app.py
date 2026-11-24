"""Insights HTTP service."""

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen

import pymssql
from flask import Flask, Response, g, jsonify, request
from stats import best_weekday, completion_rate, milestone_kinds, scheduled_day_count


def connect_database() -> pymssql.Connection:
    """Open the insights SQL Server connection."""
    parsed = urlparse(os.environ["DATABASE_URL"])
    query = parse_qs(parsed.query)
    return pymssql.connect(
        server=parsed.hostname,
        port=parsed.port or 1433,
        user=parsed.username,
        password=parsed.password,
        database=parsed.path.lstrip("/"),
        login_timeout=int(query.get("login_timeout", ["5"])[0]),
    )


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
        "@Resource = 'insights-migrations', @LockMode = 'Exclusive', "
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
            for statement in migration_path.read_text(encoding="utf-8").split(";"):
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
            "@Resource = 'insights-migrations', @LockOwner = 'Session';"
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


def call_habits(habit_id: int) -> tuple[dict[str, object] | None, int]:
    """Call the habits service with a timeout."""
    base_url = os.environ["HABITS_URL"].rstrip("/")
    if urlparse(base_url).scheme not in ("http", "https"):
        return None, 503
    timeout = float(os.environ.get("HABITS_TIMEOUT_S", "5"))
    try:
        with urlopen(  # noqa: S310
            f"{base_url}/habits/{habit_id}/public",
            timeout=timeout,
        ) as response:
            if response.status == 200:
                return json.loads(response.read().decode("utf-8")), 200
            return None, response.status
    except HTTPError as error:
        if error.code == 404:
            return None, 404
        return None, 503
    except (URLError, TimeoutError, OSError):
        return None, 503


def create_app() -> Flask:
    """Create and configure the insights Flask app."""
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
            response.headers["Access-Control-Allow-Methods"] = "GET,OPTIONS"
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

    @app.get("/insights/<int:habit_id>/weekly")
    def weekly(habit_id: int) -> tuple[Response, int]:
        """Return seven-day completion statistics."""
        habits_data, status = call_habits(habit_id)
        if status == 404:
            return jsonify(error="habit not found"), 404
        if status == 503 or habits_data is None:
            return jsonify(error="habits service unavailable"), 503
        checkins = [date.fromisoformat(value) for value in habits_data["checkin_dates"]]
        end = date.today()
        start = end - timedelta(days=6)
        window_dates = [value for value in checkins if start <= value <= end]
        due_days = scheduled_day_count(
            habits_data["scheduled_weekdays"],
            start,
            end,
        )
        return jsonify(
            habit_id=habit_id,
            window_days=7,
            scheduled_days=due_days,
            completed=len(window_dates),
            rate=completion_rate(len(window_dates), due_days),
        ), 200

    @app.get("/insights/<int:habit_id>/summary")
    def summary(habit_id: int) -> tuple[Response, int]:
        """Return streak, best weekday, and milestones."""
        habits_data, status = call_habits(habit_id)
        if status == 404:
            return jsonify(error="habit not found"), 404
        if status == 503 or habits_data is None:
            return jsonify(error="habits service unavailable"), 503
        all_dates = [date.fromisoformat(value) for value in habits_data["checkin_dates"]]
        streak = int(habits_data["streak"])
        today = date.today().isoformat()
        database = get_database()
        cursor = database.cursor(as_dict=True)
        for kind in milestone_kinds(streak):
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM milestones WHERE habit_id = %s AND kind = %s) "
                "INSERT INTO milestones (habit_id, kind, achieved_on) VALUES (%s, %s, %s)",
                (habit_id, kind, habit_id, kind, today),
            )
        database.commit()
        cursor.execute(
            "SELECT id, habit_id, kind, achieved_on FROM milestones "
            "WHERE habit_id = %s ORDER BY achieved_on, kind",
            (habit_id,),
        )
        milestones = cursor.fetchall()
        return jsonify(
            habit_id=habit_id,
            streak=streak,
            best_weekday=best_weekday(all_dates),
            milestones=milestones,
        ), 200

    @app.get("/insights/<int:habit_id>/milestones")
    def milestones(habit_id: int) -> tuple[Response, int]:
        """Return recorded milestones."""
        habits_data, status = call_habits(habit_id)
        if status == 404:
            return jsonify(error="habit not found"), 404
        if status == 503 or habits_data is None:
            return jsonify(error="habits service unavailable"), 503
        cursor = get_database().cursor(as_dict=True)
        cursor.execute(
            "SELECT id, habit_id, kind, achieved_on FROM milestones "
            "WHERE habit_id = %s ORDER BY achieved_on, kind",
            (habit_id,),
        )
        return jsonify(milestones=cursor.fetchall()), 200

    return app


app = create_app()
