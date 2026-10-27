"""Tests for root and health inspection API endpoints."""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Verifies root API metadata endpoint is responsive."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "platform" in data
    assert data["version"] == "0.1.0"
    assert data["health_endpoint"] == "/api/v1/health"


def test_health_endpoint_structure(client: TestClient):
    """Verifies /api/v1/health conforms to HealthResponse schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data
    assert "version" in data
    assert "timestamp" in data
    assert "subsystems" in data

    subsystems = data["subsystems"]
    assert "database" in subsystems
    assert "ingestion_pipeline" in subsystems
    assert "detection_engine" in subsystems
    assert "status" in subsystems["database"]
