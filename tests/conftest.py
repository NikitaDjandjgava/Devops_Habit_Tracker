import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    return create_app(data_dir=str(tmp_path)).test_client()
