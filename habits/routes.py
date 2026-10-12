"""HTTP endpoints for creating and tracking habits."""

from datetime import date

from flask import Blueprint, Response, jsonify, request

from db import get_db
from habits import public as habits_api
from habits import repository
from habits.schedule import parse_schedule

bp = Blueprint("habits", __name__, url_prefix="/habits")


@bp.post("")
def create() -> Response | tuple[Response, int]:
    """Create a habit from validated JSON input."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="request body must be a JSON object"), 400
    name = data.get("name")
    schedule = parse_schedule(data)
    if not isinstance(name, str) or not name.strip() or schedule is None:
        return jsonify(error="invalid name or schedule"), 400
    name = name.strip()
    cadence = "daily" if len(schedule["days_of_week"]) == 7 else "weekly"
    habit_id = repository.create_habit(
        get_db(),
        name,
        cadence,
        schedule["days_of_week"],
        schedule["time_of_day"],
        schedule["alert_type"],
        schedule["alert_offset_minutes"],
    )
    return jsonify(id=habit_id, name=name, cadence=cadence, **schedule), 201


@bp.get("")
def list_all() -> Response:
    """Return all habits in identifier order."""
    return jsonify(repository.list_habits(get_db()))


@bp.get("/templates")
def list_templates() -> Response:
    """Return seeded templates for API clients that use them."""
    return jsonify(repository.list_templates(get_db()))


@bp.post("/from-template/<int:template_id>")
def from_template(template_id: int) -> Response | tuple[Response, int]:
    """Create a habit from a template or return 404 when it is missing."""
    db = get_db()
    template = repository.get_template(db, template_id)
    if template is None:
        return jsonify(error="template not found"), 404
    habit_id = repository.create_habit(db, template["name"], template["cadence"])
    return jsonify(id=habit_id, name=template["name"], cadence=template["cadence"]), 201


@bp.delete("/<int:habit_id>")
def delete(habit_id: int) -> tuple[Response, int] | tuple[str, int]:
    """Permanently delete a habit and its check-ins."""
    if not repository.delete_habit(get_db(), habit_id):
        return jsonify(error="habit not found"), 404
    return "", 204


@bp.post("/<int:habit_id>/checkins")
def check_in(habit_id: int) -> Response | tuple[Response, int]:
    """Record an idempotent check-in for the requested habit."""
    db = get_db()
    if repository.get_habit(db, habit_id) is None:
        return jsonify(error="habit not found"), 404
    data = request.get_json(silent=True)
    if data is not None and not isinstance(data, dict):
        return jsonify(error="request body must be a JSON object"), 400
    if data is None:
        if request.get_data(cache=True).strip():
            return jsonify(error="request body must be valid JSON"), 400
        data = {}
    checked_on = data.get("date", date.today().isoformat())
    if not isinstance(checked_on, str):
        return jsonify(error="date must be YYYY-MM-DD"), 400
    try:
        parsed_date = date.fromisoformat(checked_on)
    except ValueError:
        return jsonify(error="date must be YYYY-MM-DD"), 400
    if parsed_date.isoformat() != checked_on:
        return jsonify(error="date must be YYYY-MM-DD"), 400
    repository.add_checkin(db, habit_id, checked_on)
    return jsonify(habit_id=habit_id, date=checked_on), 201


@bp.get("/<int:habit_id>/streak")
def streak(habit_id: int) -> Response | tuple[Response, int]:
    """Return the current cadence-aware streak or 404 for an unknown habit."""
    db = get_db()
    if not habits_api.habit_exists(db, habit_id):
        return jsonify(error="habit not found"), 404
    return jsonify(habit_id=habit_id, streak=habits_api.current_streak(db, habit_id, date.today()))
