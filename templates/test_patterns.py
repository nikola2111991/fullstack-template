"""
pytest Patterns — Fixtures, mock APIs, AAA pattern
Run: pytest tests/ -v --cov=app --cov-report=term
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    from app.main import create_app
    return create_app()

@pytest.fixture
def client(app):
    return TestClient(app)

@pytest.fixture
async def async_client(app):
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.get_all = AsyncMock(return_value=[{"id": 1, "name": "Test"}])
    db.create = AsyncMock(return_value={"id": 2, "name": "New"})
    return db

@pytest.fixture
def mock_external_api():
    with patch("app.services.external.ExternalApiClient") as mock:
        client = AsyncMock()
        client.get = AsyncMock(return_value={"data": {}, "status": 200})
        mock.return_value = client
        yield client


class TestHealth:
    def test_returns_200(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

class TestCRUD:
    def test_list_200(self, client): assert client.get("/api/v1/items").status_code == 200
    def test_not_found_404(self, client): assert client.get("/api/v1/items/99999").status_code == 404
    def test_create_201(self, client):
        r = client.post("/api/v1/items", json={"name": "Test"})
        assert r.status_code == 201
    def test_invalid_422(self, client): assert client.post("/api/v1/items", json={}).status_code == 422
    def test_unauthorized_401(self, client): assert client.get("/api/v1/protected").status_code == 401

# Naming: test_[what]_[expected] · AAA pattern · 1 test = 1 behavior
