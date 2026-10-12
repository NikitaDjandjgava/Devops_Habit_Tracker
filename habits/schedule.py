"""Validation and calculation helpers for habit schedules."""

from datetime import date, datetime, time, timedelta
from typing import TypedDict


class HabitSchedule(TypedDict):
    """Validated schedule values accepted by the habits domain."""

    days_of_week: list[int]
    time_of_day: str
    alert_type: str
    alert_offset_minutes: int


def parse_schedule(data: dict[str, object]) -> HabitSchedule | None:
    """Validate schedule fields from API or form data."""
    raw_days = data.get("days_of_week")
    if raw_days is None:
        cadence = data.get("cadence", "daily")
        raw_days = list(range(7)) if cadence == "daily" else [0] if cadence == "weekly" else None
    if not isinstance(raw_days, list) or not raw_days:
        return None
    if any(
        not isinstance(day, int) or isinstance(day, bool) or day not in range(7) for day in raw_days
    ):
        return None
    days = sorted(set(raw_days))
    if len(days) != len(raw_days):
        return None

    raw_time = data.get("time_of_day", "09:00")
    if not isinstance(raw_time, str):
        return None
    try:
        parsed_time = time.fromisoformat(raw_time)
    except ValueError:
        return None
    if parsed_time.strftime("%H:%M") != raw_time:
        return None

    alert_type = data.get("alert_type", "at_time")
    if alert_type == "at_time":
        offset = 0
    elif alert_type == "15_before":
        offset = 15
    elif alert_type == "custom":
        amount = data.get("alert_amount")
        unit = data.get("alert_unit")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 1:
            return None
        if unit == "minutes" and amount <= 1440:
            offset = amount
        elif unit == "hours" and amount <= 24:
            offset = amount * 60
        else:
            return None
    else:
        return None

    return {
        "days_of_week": days,
        "time_of_day": raw_time,
        "alert_type": str(alert_type),
        "alert_offset_minutes": offset,
    }


def current_scheduled_streak(
    checkin_dates: list[date], days_of_week: list[int], today: date
) -> int:
    """Count completed scheduled dates back from the latest due date."""
    checked_dates = set(checkin_dates)
    selected_days = set(days_of_week)
    if not checked_dates or not selected_days:
        return 0

    current_date = today
    while current_date.weekday() not in selected_days:
        current_date -= timedelta(days=1)
    if current_date == today and current_date not in checked_dates:
        current_date -= timedelta(days=1)
        while current_date.weekday() not in selected_days:
            current_date -= timedelta(days=1)

    streak = 0
    while current_date in checked_dates:
        streak += 1
        current_date -= timedelta(days=1)
        while current_date.weekday() not in selected_days:
            current_date -= timedelta(days=1)
    return streak


def due_reminders(habits: list[dict[str, object]], now: datetime) -> list[dict[str, object]]:
    """Return schedule reminders whose alert time matches the provided local minute."""
    reminders = []
    for habit in habits:
        days = habit["days_of_week"]
        scheduled_time = habit["time_of_day"]
        offset = habit["alert_offset_minutes"]
        checked_dates = habit["checkin_dates"]
        if not isinstance(days, list) or not isinstance(scheduled_time, str):
            continue
        if not isinstance(offset, int) or not isinstance(checked_dates, list):
            continue
        for day_offset in (0, 1):
            event_date = now.date() + timedelta(days=day_offset)
            if event_date.weekday() not in days or event_date.isoformat() in checked_dates:
                continue
            event_time = datetime.combine(event_date, time.fromisoformat(scheduled_time))
            alert_time = event_time - timedelta(minutes=offset)
            if (
                alert_time.date() == now.date()
                and alert_time.hour == now.hour
                and alert_time.minute == now.minute
            ):
                reminders.append(
                    {
                        "id": habit["id"],
                        "name": habit["name"],
                        "time": scheduled_time,
                        "date": event_date.isoformat(),
                    }
                )
    return reminders
