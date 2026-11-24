"""Tests for the habits HTTP service."""

import importlib
import sys
from pathlib import Path

import pytest


def load_habits_app() -> object:
    """Load the habits app after test setup."""
    sys.modules.pop("app", None)
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root / "services" / "habits"))
    module = importlib.import_module("app")
    return module


def test_database_url_parses_service_connection() -> None:
    service_app = load_habits_app()
    settings = service_app.parse_database_url(
        "mssql://habits_login:local_password@sqlserver:1433/habits_db"
        "?login_timeout=7"
    )
    assert settings["server"] == "sqlserver"
    assert settings["port"] == 1433
    assert settings["database"] == "habits_db"
    assert settings["login_timeout"] == 7


class FakeCursor:
    """Minimal SQL cursor for Flask route tests."""

    def __init__(self) -> None:
        self.rowcount = 1

    def execute(self, _statement: str, _parameters: object = None) -> None:
        return None

    def fetchone(self) -> dict[str, int]:
        return {"ok": 1}

    def fetchall(self) -> list[dict[str, object]]:
        return []


class FakeDatabase:
    """Minimal SQL connection for Flask route tests."""

    def cursor(self, as_dict: bool = False) -> FakeCursor:
        return FakeCursor()

    def rollback(self) -> None:
        return None

    def close(self) -> None:
        return None


def test_health_reports_database_state_and_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    service_app = load_habits_app()
    monkeypatch.setenv("UI_ORIGIN", "https://ui.example")
    monkeypatch.setenv("GIT_SHA", "test-sha")
    monkeypatch.setattr(service_app, "connect_database", FakeDatabase)

    client = service_app.create_app().test_client()
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "status": "ok",
        "db": "ok",
        "version": "test-sha",
    }
    assert response.headers["Access-Control-Allow-Origin"] == "https://ui.example"
