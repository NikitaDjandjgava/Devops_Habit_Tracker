from datetime import date

from flask import Blueprint, jsonify, request

from db import get_db
from habits import repository
from habits.streaks import current_daily_streak

bp = Blueprint("habits", __name__, url_prefix="/habits")


@bp.post("")
def create():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    cadence = data.get("cadence", "daily")
    if not name or cadence not in ("daily", "weekly"):
        return jsonify(error="name required; cadence must be 'daily' or 'weekly'"), 400
    habit_id = repository.create_habit(get_db(), name, cadence)
    return jsonify(id=habit_id, name=name, cadence=cadence), 201


@bp.get("")
def list_all():
    return jsonify(repository.list_habits(get_db()))


@bp.post("/<int:habit_id>/checkins")
def check_in(habit_id):
    db = get_db()
    if repository.get_habit(db, habit_id) is None:
        return jsonify(error="habit not found"), 404
    data = request.get_json(silent=True) or {}
    checked_on = data.get("date") or date.today().isoformat()
    try:
        date.fromisoformat(checked_on)
    except ValueError:
        return jsonify(error="date must be YYYY-MM-DD"), 400
    repository.add_checkin(db, habit_id, checked_on)
    return jsonify(habit_id=habit_id, date=checked_on), 201


@bp.get("/<int:habit_id>/streak")
def streak(habit_id):
    db = get_db()
    if repository.get_habit(db, habit_id) is None:
        return jsonify(error="habit not found"), 404
    dates = [date.fromisoformat(d) for d in repository.get_checkin_dates(db, habit_id)]
    return jsonify(habit_id=habit_id, streak=current_daily_streak(dates, date.today()))
