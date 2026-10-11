from datetime import date

from flask import Blueprint, jsonify, request

from db import get_db
from habits import public as habits_api
from habits import repository

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


@bp.get("/templates")
def list_templates():
    return jsonify(repository.list_templates(get_db()))


@bp.post("/from-template/<int:template_id>")
def from_template(template_id):
    db = get_db()
    template = repository.get_template(db, template_id)
    if template is None:
        return jsonify(error="template not found"), 404
    habit_id = repository.create_habit(db, template["name"], template["cadence"])
    return jsonify(id=habit_id, name=template["name"], cadence=template["cadence"]), 201


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
    if not habits_api.habit_exists(db, habit_id):
        return jsonify(error="habit not found"), 404
    return jsonify(habit_id=habit_id, streak=habits_api.current_streak(db, habit_id, date.today()))
