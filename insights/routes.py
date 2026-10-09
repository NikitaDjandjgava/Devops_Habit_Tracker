from datetime import date, timedelta

from flask import Blueprint, jsonify

from db import get_db
from habits import public as habits_api  # seam: only import from habits.public
from insights.stats import completion_rate

bp = Blueprint("insights", __name__, url_prefix="/insights")

WINDOW_DAYS = 7


@bp.get("/<int:habit_id>/weekly")
def weekly(habit_id):
    end = date.today()
    start = end - timedelta(days=WINDOW_DAYS - 1)
    dates = habits_api.checkin_dates(get_db(), habit_id, start.isoformat(), end.isoformat())
    return jsonify(
        habit_id=habit_id,
        window_days=WINDOW_DAYS,
        completed=len(dates),
        rate=completion_rate(len(dates), WINDOW_DAYS),
    )
