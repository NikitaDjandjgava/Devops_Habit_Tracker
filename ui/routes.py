"""HTML dashboard routes for interacting with habits."""

from datetime import date, datetime, timedelta

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from werkzeug.wrappers import Response

from db import get_db
from habits import public as habits_api
from habits import repository
from habits.schedule import due_reminders, parse_schedule

bp = Blueprint("ui", __name__)
WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


@bp.get("/")
def dashboard() -> str:
    """Render today's habits and progress summary."""
    db = get_db()
    today = date.today()
    habits = repository.list_habits(db)
    completed_count = 0

    for habit in habits:
        start_date = today - timedelta(days=6)
        dates = habits_api.checkin_dates(
            db,
            habit["id"],
            start_date.isoformat(),
            today.isoformat(),
        )
        habit["checkin_dates"] = dates
        habit["completed"] = today.isoformat() in dates
        habit["scheduled_today"] = today.weekday() in habit["days_of_week"]
        habit["streak"] = habits_api.current_streak(db, habit["id"], today)
        habit["period_label"] = "TODAY" if habit["scheduled_today"] else "NOT TODAY"
        habit["streak_label"] = "day streak"
        habit["schedule_label"] = "Every day" if len(habit["days_of_week"]) == 7 else "Custom days"
        habit["days_label"] = ", ".join(WEEKDAY_NAMES[day] for day in habit["days_of_week"])
        habit["time_label"] = (
            datetime.strptime(habit["time_of_day"], "%H:%M").strftime("%I:%M %p").lstrip("0")
        )
        offset = habit["alert_offset_minutes"]
        if offset == 0:
            habit["alert_label"] = "At event time"
        elif offset == 15:
            habit["alert_label"] = "15 min before"
        elif offset % 60 == 0:
            habit["alert_label"] = f"{offset // 60} hr before"
        else:
            habit["alert_label"] = f"{offset} min before"
        completed_count += int(habit["completed"] and habit["scheduled_today"])

    scheduled_habits = [habit for habit in habits if habit["scheduled_today"]]
    completion_percent = (
        round(completed_count * 100 / len(scheduled_habits)) if scheduled_habits else 0
    )
    reminder_habits = []
    for habit in scheduled_habits:
        if not habit["completed"]:
            reminder_habits.append(habit)
    return render_template(
        "dashboard.html",
        habits=habits,
        scheduled_habits=scheduled_habits,
        reminder_habits=reminder_habits,
        today=today,
        completed_count=completed_count,
        completion_percent=completion_percent,
    )


@bp.post("/ui/habits")
def create_habit() -> Response:
    """Create a habit from the dashboard form."""
    name = request.form.get("name", "").strip()
    raw_days = request.form.getlist("days_of_week")
    try:
        selected_days = [int(day) for day in raw_days]
    except ValueError:
        selected_days = []
    form_data: dict[str, object] = {
        "days_of_week": selected_days,
        "time_of_day": request.form.get("time_of_day", ""),
        "alert_type": request.form.get("alert_type", ""),
    }
    if form_data["alert_type"] == "custom":
        try:
            form_data["alert_amount"] = int(request.form.get("alert_amount", ""))
        except ValueError:
            form_data["alert_amount"] = 0
        form_data["alert_unit"] = request.form.get("alert_unit", "")
    schedule = parse_schedule(form_data)
    if not name or schedule is None:
        flash("Enter a habit name and choose valid schedule and alert details.", "error")
        return redirect(url_for("ui.dashboard"))

    cadence = "daily" if len(schedule["days_of_week"]) == 7 else "weekly"
    repository.create_habit(
        get_db(),
        name,
        cadence,
        schedule["days_of_week"],
        schedule["time_of_day"],
        schedule["alert_type"],
        schedule["alert_offset_minutes"],
    )
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
    if today.weekday() not in habit["days_of_week"]:
        flash(f'"{habit["name"]}" is not scheduled for today.', "error")
        return redirect(url_for("ui.dashboard"))
    if today.isoformat() in habits_api.checkin_dates(
        db, habit_id, today.isoformat(), today.isoformat()
    ):
        repository.delete_checkin(db, habit_id, today.isoformat())
        flash(f'"{habit["name"]}" marked incomplete.', "success")
    else:
        repository.add_checkin(db, habit_id, today.isoformat())
        flash(f'"{habit["name"]}" completed. Nice work!', "success")
    return redirect(url_for("ui.dashboard"))


@bp.get("/ui/reminders")
def reminders() -> Response | tuple[Response, int]:
    """Return reminders due during the current browser-local minute."""
    db = get_db()
    current_time = request.args.get("now", "")
    try:
        now = datetime.fromisoformat(current_time)
    except ValueError:
        return jsonify(error="now must be a local ISO date and time"), 400
    if now.tzinfo is not None or now.strftime("%Y-%m-%dT%H:%M") != current_time:
        return jsonify(error="now must use YYYY-MM-DDTHH:MM local time"), 400
    event_start = now.date()
    event_end = event_start + timedelta(days=1)
    habits = repository.list_habits(db)
    for habit in habits:
        habit["checkin_dates"] = repository.get_checkin_dates(
            db, habit["id"], event_start.isoformat(), event_end.isoformat()
        )
    return jsonify(reminders=due_reminders(habits, now))
