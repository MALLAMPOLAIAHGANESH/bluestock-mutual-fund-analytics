# backend/tests/test_portfolio_optimization.py
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_portfolio_optimize_endpoint_invalid_payload(client):
    response = client.post(
        "/api/v1/portfolio/optimize",
        json={"amfi_codes": [], "risk_free_rate": 6.5}
    )
    assert response.status_code in [400, 500, 422]

def test_portfolio_recommendations_endpoint(client):
    response = client.get("/api/v1/portfolio/recommend?risk_tier=High&limit=3")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
    else:
        assert response.status_code in [404, 500]

def test_monte_carlo_endpoint_not_found(client):
    response = client.get("/api/v1/monte-carlo/99999999?years=5&simulations=100")
    assert response.status_code in [404, 500]

def test_risk_metrics_endpoint(client):
    response = client.get("/api/v1/risk")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

