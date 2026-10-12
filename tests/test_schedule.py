from datetime import date, datetime, timedelta

from habits.schedule import current_scheduled_streak, due_reminders, parse_schedule


def test_parse_schedule_converts_custom_hours_to_minutes() -> None:
    schedule = parse_schedule(
        {
            "days_of_week": [0, 2, 4],
            "time_of_day": "07:30",
            "alert_type": "custom",
            "alert_amount": 2,
            "alert_unit": "hours",
        }
    )
    assert schedule is not None
    assert schedule["alert_offset_minutes"] == 120


def test_parse_schedule_rejects_duplicate_or_invalid_days() -> None:
    assert parse_schedule({"days_of_week": [1, 1], "time_of_day": "09:00"}) is None
    assert parse_schedule({"days_of_week": [7], "time_of_day": "09:00"}) is None


def test_scheduled_streak_counts_only_selected_days() -> None:
    today = date(2026, 10, 12)
    completed_days = [date(2026, 10, 12), date(2026, 10, 9), date(2026, 10, 7)]
    assert current_scheduled_streak(completed_days, [0, 2, 4], today) == 3


def test_due_reminders_matches_custom_alert_time_and_skips_completed() -> None:
    now = datetime(2026, 10, 12, 7, 0)
    habit = {
        "id": 5,
        "name": "Walk",
        "days_of_week": [0],
        "time_of_day": "09:00",
        "alert_offset_minutes": 120,
        "checkin_dates": [],
    }
    reminders = due_reminders([habit], now)
    assert reminders == [{"id": 5, "name": "Walk", "time": "09:00", "date": "2026-10-12"}]

    habit["checkin_dates"] = [now.date().isoformat()]
    assert due_reminders([habit], now) == []


def test_due_reminder_handles_alert_before_midnight_for_next_day() -> None:
    now = datetime(2026, 10, 12, 23, 30)
    habit = {
        "id": 8,
        "name": "Journal",
        "days_of_week": [1],
        "time_of_day": "00:30",
        "alert_offset_minutes": 60,
        "checkin_dates": [],
    }
    assert due_reminders([habit], now)[0]["date"] == (now.date() + timedelta(days=1)).isoformat()
