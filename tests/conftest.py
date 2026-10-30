import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import repository


@pytest.fixture()
def client() -> TestClient:
    repository.clear()
    with TestClient(app) as test_client:
        yield test_client
    repository.clear()
