"""HTML dashboard routes for interacting with habits."""

from datetime import date, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from db import get_db
from habits import public as habits_api
from habits import repository

bp = Blueprint("ui", __name__)


@bp.get("/")
def dashboard() -> str:
    """Render today's habits and progress summary."""
    db = get_db()
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    habits = repository.list_habits(db)
    completed_count = 0

    for habit in habits:
        start_date = today if habit["cadence"] == "daily" else week_start
        dates = habits_api.checkin_dates(
            db,
            habit["id"],
            start_date.isoformat(),
            today.isoformat(),
        )
        habit["completed"] = bool(dates)
        habit["streak"] = habits_api.current_streak(db, habit["id"], today)
        habit["period_label"] = "TODAY" if habit["cadence"] == "daily" else "THIS WEEK"
        habit["streak_label"] = "day streak" if habit["cadence"] == "daily" else "week streak"
        completed_count += int(habit["completed"])

    templates = repository.list_templates(db)
    completion_percent = round(completed_count * 100 / len(habits)) if habits else 0
    return render_template(
        "dashboard.html",
        habits=habits,
        templates=templates,
        today=today,
        completed_count=completed_count,
        completion_percent=completion_percent,
    )


@bp.post("/ui/habits")
def create_habit() -> Response:
    """Create a habit from the dashboard form."""
    name = request.form.get("name", "").strip()
    cadence = request.form.get("cadence", "daily")
    if not name or cadence not in ("daily", "weekly"):
        flash("Enter a habit name and choose a valid schedule.", "error")
        return redirect(url_for("ui.dashboard"))

    repository.create_habit(get_db(), name, cadence)
    flash(f'"{name}" is ready to track.', "success")
    return redirect(url_for("ui.dashboard"))


@bp.post("/ui/habits/<int:habit_id>/toggle")
def toggle_checkin(habit_id: int) -> Response:
    """Toggle the current period's completion state from the dashboard."""
    db = get_db()
    habit = repository.get_habit(db, habit_id)
    if habit is None:
        flash("That habit could not be found.", "error")
        return redirect(url_for("ui.dashboard"))

    today = date.today()
    start_date = today
    if habit["cadence"] == "weekly":
        start_date = today - timedelta(days=today.weekday())
    dates = habits_api.checkin_dates(
        db,
        habit_id,
        start_date.isoformat(),
        today.isoformat(),
    )
    if dates:
        repository.delete_checkin(db, habit_id, dates[-1])
        flash(f'"{habit["name"]}" marked incomplete.', "success")
    else:
        repository.add_checkin(db, habit_id, today.isoformat())
        flash(f'"{habit["name"]}" completed. Nice work!', "success")
    return redirect(url_for("ui.dashboard"))
