from datetime import date

from habits.agenda import (
    PALETTE_SIZE,
    habit_color,
    hourly_slots,
    month_date_range,
    month_weeks,
    parse_month,
    shift_month,
)

TODAY = date(2026, 10, 12)  # a Monday
HABITS = [
    {"id": 1, "name": "Gym", "days_of_week": [0, 2, 4], "time_of_day": "18:30"},
    {"id": 2, "name": "Read", "days_of_week": [0, 1, 2, 3, 4, 5, 6], "time_of_day": "07:00"},
]


def test_habit_color_differs_for_consecutive_ids_and_wraps() -> None:
    assert habit_color(1) != habit_color(2)
    assert habit_color(1) == habit_color(1 + PALETTE_SIZE)


def test_parse_month_reads_valid_value_and_falls_back_on_invalid() -> None:
    assert parse_month("2026-02", TODAY) == (2026, 2)
    assert parse_month("not-a-month", TODAY) == (2026, 10)
    assert parse_month("", TODAY) == (2026, 10)


def test_shift_month_crosses_year_boundaries() -> None:
    assert shift_month(2026, 12, 1) == "2027-01"
    assert shift_month(2026, 1, -1) == "2025-12"


def test_month_date_range_starts_monday_and_covers_whole_month() -> None:
    first_day, last_day = month_date_range(2026, 10)
    assert first_day == date(2026, 9, 28)
    assert first_day.weekday() == 0
    assert last_day == date(2026, 11, 1)


def test_month_weeks_lists_habits_on_scheduled_days_in_time_order() -> None:
    weeks = month_weeks(2026, 10, HABITS, {(1, "2026-10-12")})
    days = {}
    for week in weeks:
        for day in week:
            days[day["date"]] = day

    monday = days[date(2026, 10, 12)]
    assert [entry["name"] for entry in monday["habits"]] == ["Read", "Gym"]
    assert monday["habits"][1]["done"] is True
    assert monday["habits"][0]["done"] is False
    assert [entry["name"] for entry in days[date(2026, 10, 13)]["habits"]] == ["Read"]
    assert days[date(2026, 9, 28)]["in_month"] is False


def test_hourly_slots_places_habits_in_their_hour() -> None:
    slots = hourly_slots(HABITS, TODAY, set())
    assert len(slots) == 24
    assert slots[0]["label"] == "12 AM"
    assert slots[18]["label"] == "6 PM"
    assert [entry["name"] for entry in slots[7]["habits"]] == ["Read"]
    assert [entry["name"] for entry in slots[18]["habits"]] == ["Gym"]

    tuesday_slots = hourly_slots(HABITS, date(2026, 10, 13), set())
    assert tuesday_slots[18]["habits"] == []
