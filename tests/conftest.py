from pathlib import Path

import pytest
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture
def client(tmp_path: Path) -> FlaskClient:
    return create_app(data_dir=str(tmp_path)).test_client()
