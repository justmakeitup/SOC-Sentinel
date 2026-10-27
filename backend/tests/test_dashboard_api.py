"""Tests for dashboard overview, alerts listing, and incidents queries."""

from fastapi.testclient import TestClient


def test_dashboard_summary_empty(client: TestClient):
    """Verifies dashboard summary returns zeroed operational counters when empty."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert "events_processed" in data
    assert "active_alerts" in data
    assert "open_incidents" in data
    assert "critical_alerts" in data
    assert "event_volume_timeseries" in data
    assert "severity_distribution" in data
    assert isinstance(data["event_volume_timeseries"], list)
    assert isinstance(data["severity_distribution"], dict)


def test_alerts_listing_empty(client: TestClient):
    """Verifies alerts endpoint returns valid paginated structure when empty."""
    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_count"] == 0
    assert data["page"] == 1
    assert data["page_size"] == 10


def test_incidents_listing_empty(client: TestClient):
    """Verifies incidents endpoint returns valid paginated structure when empty."""
    response = client.get("/api/v1/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total_count"] == 0
