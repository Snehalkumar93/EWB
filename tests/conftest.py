import os
import tempfile
import pytest
from sqlalchemy import create_engine

# Set DATABASE_URL to an isolated temporary SQLite database before any test or app module imports
_temp_dir = tempfile.mkdtemp(prefix="test_students_db_")
_default_test_db = os.path.join(_temp_dir, "test_students.db").replace("\\", "/")
os.environ["DATABASE_URL"] = f"sqlite:///{_default_test_db}"

from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def temp_db_file(tmp_path):
    """Provide a path to a fresh temporary SQLite database file for isolated tests."""
    return tmp_path / "temp_test_students.db"


@pytest.fixture
def temp_engine(temp_db_file):
    """Provide an isolated SQLAlchemy engine bound to a temporary SQLite database file."""
    db_url = f"sqlite:///{temp_db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    yield engine
    engine.dispose()


@pytest.fixture
def test_client():
    """FastAPI TestClient instance with lifespan enabled."""
    with TestClient(app) as client:
        yield client
