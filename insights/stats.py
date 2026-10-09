"""Pure insight computations (no DB)."""


def completion_rate(done_days, window_days):
    """Fraction of days in the window that were completed, 0.0 to 1.0."""
    if window_days <= 0:
        raise ValueError("window_days must be positive")
    return min(done_days, window_days) / window_days


# TODO: best_weekday(checkin_dates) and milestone detection (e.g. 'streak_7')
