"""Pure calendar and hourly-timeline layout for scheduled habits (no DB)."""

import calendar
from datetime import date, datetime
from typing import Any

HabitRow = dict[str, Any]

# Must match the number of .habit-color-N classes in static/dashboard.css.
PALETTE_SIZE = 8


def habit_color(habit_id: int) -> int:
    """Pick a palette slot so consecutively created habits get different colors."""
    return habit_id % PALETTE_SIZE


def _habit_time(habit: HabitRow) -> str:
    """Return the sort key that orders habits by their time of day."""
    return habit["time_of_day"]


def _entry(habit: HabitRow, day: date, checked: set[tuple[int, str]]) -> HabitRow:
    """Build the display entry for one habit on one date."""
    return {
        "id": habit["id"],
        "name": habit["name"],
        "time": habit["time_of_day"],
        "color": habit_color(habit["id"]),
        "done": (habit["id"], day.isoformat()) in checked,
    }


def parse_month(value: str, today: date) -> tuple[int, int]:
    """Read a YYYY-MM query value, falling back to the current month when invalid."""
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError:
        return today.year, today.month
    return parsed.year, parsed.month


def shift_month(year: int, month: int, step: int) -> str:
    """Return the YYYY-MM label that is step months away from the given month."""
    month_index = year * 12 + (month - 1) + step
    return f"{month_index // 12:04d}-{month_index % 12 + 1:02d}"


def month_date_range(year: int, month: int) -> tuple[date, date]:
    """Return the first and last dates shown on a Monday-first month grid."""
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    return weeks[0][0], weeks[-1][-1]


def month_weeks(
    year: int, month: int, habits: list[HabitRow], checked: set[tuple[int, str]]
) -> list[list[HabitRow]]:
    """Group the month grid into weeks, listing each habit on its scheduled weekdays."""
    ordered_habits = sorted(habits, key=_habit_time)
    weeks = []
    for week_dates in calendar.Calendar(firstweekday=0).monthdatescalendar(year, month):
        week = []
        for day in week_dates:
            entries = []
            for habit in ordered_habits:
                if day.weekday() in habit["days_of_week"]:
                    entries.append(_entry(habit, day, checked))
            week.append({"date": day, "in_month": day.month == month, "habits": entries})
        weeks.append(week)
    return weeks


def hourly_slots(
    habits: list[HabitRow], day: date, checked: set[tuple[int, str]]
) -> list[HabitRow]:
    """Place the habits scheduled on a date into 24 one-hour slots."""
    slots: list[HabitRow] = []
    for hour in range(24):
        label = datetime(2000, 1, 1, hour).strftime("%I %p").lstrip("0")
        slots.append({"hour": hour, "label": label, "habits": []})
    for habit in sorted(habits, key=_habit_time):
        if day.weekday() in habit["days_of_week"]:
            hour = int(habit["time_of_day"][:2])
            slots[hour]["habits"].append(_entry(habit, day, checked))
    return slots
