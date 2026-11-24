"""Test setup for service modules."""

import sys
import types
from pathlib import Path

import pytest


class FakePymssqlError(Exception):
    """Stand-in for pymssql errors on a Windows test interpreter."""


def install_pymssql_stub() -> None:
    """Allow service modules to import when local Python lacks pymssql."""
    module = types.ModuleType("pymssql")
    module.Connection = object
    module.Error = FakePymssqlError
    module.connect = lambda **_settings: None
    sys.modules["pymssql"] = module


@pytest.fixture(scope="session", autouse=True)
def service_import_setup() -> None:
    """Expose copied Docker modules under their runtime names."""
    install_pymssql_stub()
    root = Path(__file__).parent.parent
    sys.path.insert(0, str(root))

    import habits.schedule as schedule_module

    sys.modules["schedule"] = schedule_module

    import insights.stats as stats_module

    sys.modules["stats"] = stats_module
