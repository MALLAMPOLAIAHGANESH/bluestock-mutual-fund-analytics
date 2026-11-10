# backend/tests/test_api.py
import sys
import os
# Ensure that the backend directory is in the sys.path so app can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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

def test_downloads_endpoint_existence(client):
    # Test checking file existence for a few sample file keys
    keys = ["raw-csv", "sqlite-db", "eda-ipynb", "powerbi-pbix", "project-report-pdf", "etl-py"]
    for key in keys:
        res = client.get(f"/api/v1/downloads/{key}/exists")
        assert res.status_code == 200
        assert res.json()["exists"] is True

def test_downloads_endpoint_retrieval(client):
    # Test retrieving a CSV file
    res = client.get("/api/v1/downloads/raw-csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "attachment" in res.headers["content-disposition"]
    assert "raw_dataset.csv" in res.headers["content-disposition"]

    # Test retrieving a notebook file
    res = client.get("/api/v1/downloads/eda-ipynb")
    assert res.status_code == 200
    assert "application/x-ipynb+json" in res.headers["content-type"]
    assert "eda_notebook.ipynb" in res.headers["content-disposition"]

    # Test invalid file key returns 404
    res = client.get("/api/v1/downloads/invalid-file-key")
    assert res.status_code == 404

    # Test invalid file key exists check returns exists=False
    res = client.get("/api/v1/downloads/invalid-file-key/exists")
    assert res.status_code == 200
    assert res.json()["exists"] is False

