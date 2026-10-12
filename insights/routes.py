"""HTTP endpoints for habit statistics and milestones."""

from datetime import date, timedelta

from flask import Blueprint, Response, jsonify

from db import get_db
from habits import public as habits_api  # seam: only import from habits.public
from insights import repository
from insights.stats import best_weekday, completion_rate, scheduled_day_count

bp = Blueprint("insights", __name__, url_prefix="/insights")

WINDOW_DAYS = 7


@bp.get("/<int:habit_id>/weekly")
def weekly(habit_id: int) -> Response | tuple[Response, int]:
    """Return seven-day completion statistics for a habit."""
    db = get_db()
    if not habits_api.habit_exists(db, habit_id):
        return jsonify(error="habit not found"), 404
    end = date.today()
    start = end - timedelta(days=WINDOW_DAYS - 1)
    dates = habits_api.checkin_dates(db, habit_id, start.isoformat(), end.isoformat())
    due_days = scheduled_day_count(habits_api.scheduled_weekdays(db, habit_id), start, end)
    return jsonify(
        habit_id=habit_id,
        window_days=WINDOW_DAYS,
        scheduled_days=due_days,
        completed=len(dates),
        rate=completion_rate(len(dates), due_days),
    )


@bp.get("/<int:habit_id>/milestones")
def milestones(habit_id: int) -> Response | tuple[Response, int]:
    """Return recorded milestones or 404 when the habit is missing."""
    db = get_db()
    if not habits_api.habit_exists(db, habit_id):
        return jsonify(error="habit not found"), 404
    return jsonify(milestones=repository.list_milestones(db, habit_id))


@bp.get("/<int:habit_id>/summary")
def summary(habit_id: int) -> Response | tuple[Response, int]:
    """Return the current streak, best weekday, and recorded milestones."""
    db = get_db()
    if not habits_api.habit_exists(db, habit_id):
        return jsonify(error="habit not found"), 404

    today = date.today()
    all_dates = [date.fromisoformat(d) for d in habits_api.checkin_dates(db, habit_id)]
    streak = habits_api.current_streak(db, habit_id, today)
    milestones = repository.record_milestones(db, habit_id, today.isoformat(), streak)

    return jsonify(
        habit_id=habit_id,
        streak=streak,
        best_weekday=best_weekday(all_dates),
        milestones=milestones,
    )
