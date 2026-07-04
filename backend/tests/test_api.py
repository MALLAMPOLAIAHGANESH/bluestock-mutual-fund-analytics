# backend/tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Setup test tables
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_dashboard_endpoint(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code in [200, 500]

def test_funds_endpoint(client):
    response = client.get("/api/v1/funds")
    assert response.status_code in [200, 500]

def test_risk_endpoint(client):
    response = client.get("/api/v1/risk")
    assert response.status_code in [200, 500]
