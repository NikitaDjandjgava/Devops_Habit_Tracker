"""Pure insight computations (no DB)."""
import calendar
from collections import Counter
from datetime import date


def completion_rate(done_days, window_days):
    """Fraction of days in the window that were completed, 0.0 to 1.0."""
    if window_days <= 0:
        raise ValueError("window_days must be positive")
    return min(done_days, window_days) / window_days


def best_weekday(checkin_dates):
    """Return the weekday with the most check-ins; tie-breaks by earliest weekday."""
    if not checkin_dates:
        return None

    counts = Counter()
    for value in checkin_dates:
        if hasattr(value, "weekday"):
            day = value.strftime("%A")
        else:
            day = date.fromisoformat(value).strftime("%A")
        counts[day] += 1

    weekday_rank = {day: index for index, day in enumerate(calendar.day_name)}
    return max(counts.items(), key=lambda item: (item[1], -weekday_rank[item[0]]))[0]


def milestone_kinds(streak_value):
    """Return milestone names that are achieved at this streak length."""
    targets = (7, 30, 90, 365)
    return [f"streak_{target}" for target in targets if streak_value >= target]
