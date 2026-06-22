import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "KAVACH Backend is running with full routers!"}

def test_get_graph():
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "nodes" in data["data"]
    assert "links" in data["data"]
    assert "campaigns" in data["data"]
    assert len(data["data"]["campaigns"]) >= 3 # We seeded 3 campaigns

def test_get_districts():
    response = client.get("/api/districts")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 4 # We seeded 4 districts

def test_get_district_summary():
    # Jamtara was explicitly seeded
    response = client.get("/api/districts/Jamtara/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Jamtara"
    assert "active_campaigns" in data["data"]

def test_get_invalid_district_summary():
    response = client.get("/api/districts/Gotham/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "error" in data
