import pytest

from insights.stats import completion_rate


def test_completion_rate():
    assert completion_rate(3, 7) == pytest.approx(3 / 7)


def test_rate_is_capped_at_one():
    assert completion_rate(10, 7) == 1.0


def test_invalid_window_raises():
    with pytest.raises(ValueError):
        completion_rate(1, 0)
