from datetime import date

import pytest

from insights.stats import completion_rate, scheduled_day_count


def test_completion_rate() -> None:
    assert completion_rate(3, 7) == pytest.approx(3 / 7)


def test_rate_is_capped_at_one() -> None:
    assert completion_rate(10, 7) == 1.0


def test_invalid_window_raises() -> None:
    with pytest.raises(ValueError):
        completion_rate(1, 0)


def test_scheduled_day_count_only_counts_selected_weekdays() -> None:
    monday = date(2026, 10, 5)
    sunday = date(2026, 10, 11)
    assert scheduled_day_count([0, 2, 4], monday, sunday) == 3
    assert scheduled_day_count([0], monday, sunday) == 1
