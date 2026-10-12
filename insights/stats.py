"""Pure insight computations (no DB)."""

import calendar
from collections import Counter
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import TypeAlias

CheckinDate: TypeAlias = date | datetime | str


def completion_rate(done_days: int, window_days: int) -> float:
    """Calculate the completed fraction of a window, capped at one."""
    if window_days <= 0:
        raise ValueError("window_days must be positive")
    return min(done_days, window_days) / window_days


def scheduled_day_count(days_of_week: list[int], start: date, end: date) -> int:
    """Count dates from start to end inclusive that fall on a scheduled weekday."""
    count = 0
    current_date = start
    while current_date <= end:
        if current_date.weekday() in days_of_week:
            count += 1
        current_date += timedelta(days=1)
    return count


def best_weekday(checkin_dates: Sequence[CheckinDate]) -> str | None:
    """Return the weekday with most check-ins, breaking ties Monday-first."""
    if not checkin_dates:
        return None

    counts: Counter[str] = Counter()
    for value in checkin_dates:
        if isinstance(value, str):
            checked_date = date.fromisoformat(value)
        elif isinstance(value, datetime):
            checked_date = value.date()
        else:
            checked_date = value
        day = checked_date.strftime("%A")
        counts[day] += 1

    weekday_rank = {day: index for index, day in enumerate(calendar.day_name)}
    return max(counts.items(), key=lambda item: (item[1], -weekday_rank[item[0]]))[0]


def milestone_kinds(streak_value: int) -> list[str]:
    """List supported streak milestones reached at the given streak length."""
    targets = (7, 30, 90, 365)
    return [f"streak_{target}" for target in targets if streak_value >= target]
