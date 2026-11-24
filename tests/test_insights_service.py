"""Tests for the insights HTTP service."""

import importlib
import sys
from pathlib import Path

import pytest


def load_insights_app() -> object:
    """Load the insights app after test setup."""
    sys.modules.pop("app", None)
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root / "services" / "insights"))
    module = importlib.import_module("app")
    return module


def test_habits_call_returns_designed_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service_app = load_insights_app()
    monkeypatch.setenv("HABITS_URL", "http://habits:8000")
    monkeypatch.setenv("HABITS_TIMEOUT_S", "1")

    def timeout_error(*_args: object, **_kwargs: object) -> None:
        raise TimeoutError()

    monkeypatch.setattr(service_app, "urlopen", timeout_error)
    result, status = service_app.call_habits(42)

    assert result is None
    assert status == 503


def test_habits_call_returns_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    service_app = load_insights_app()
    monkeypatch.setenv("HABITS_URL", "http://habits:8000")

    def not_found(*_args: object, **_kwargs: object) -> None:
        raise service_app.HTTPError(
            "http://habits:8000",
            404,
            "not found",
            {},
            None,
        )

    monkeypatch.setattr(service_app, "urlopen", not_found)
    result, status = service_app.call_habits(99)

    assert result is None
    assert status == 404
