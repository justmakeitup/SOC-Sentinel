"""Comprehensive test suite for the log ingestion subsystem.

Validates parsing, normalization, Pydantic validation, malformed row quarantine,
upload limits, idempotency, timestamp handling, and API endpoints.
"""

import io

from fastapi.testclient import TestClient


def test_import_valid_auth_csv(client: TestClient):
    """Imports synthetic authentication logs formatted as CSV."""
    csv_data = (
        "timestamp,user,action,source_ip,host\n"
        "2026-10-27T10:00:00Z,johndoe,login_success,192.168.1.10,workstation-01\n"
        "2026-10-27T10:01:00Z,admin,login_failed,192.168.1.50,server-dc01\n"
        "2026-10-27T10:02:00Z,admin,account_locked,192.168.1.50,server-dc01\n"
    )

    files = {"file": ("auth_logs.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/ingestion/upload", files=files, data={"parser_type": "auth"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["events_processed"] == 3
    assert data["events_failed"] == 0
    assert data["is_duplicate_batch"] is False

    # Verify events are accessible via events endpoint
    events_res = client.get("/api/v1/events?event_type=authentication")
    assert events_res.status_code == 200
    ev_data = events_res.json()
    assert ev_data["total_count"] >= 3


def test_import_valid_firewall_json(client: TestClient):
    """Imports synthetic firewall flow logs formatted as a JSON array."""
    json_data = [
        {
            "timestamp": "2026-10-27T10:05:00Z",
            "action": "ALLOW",
            "src_ip": "10.0.1.15",
            "src_port": 54321,
            "dst_ip": "172.16.0.4",
            "dst_port": 443,
            "protocol": "TCP",
        },
        {
            "timestamp": "2026-10-27T10:06:00Z",
            "action": "BLOCK",
            "src_ip": "203.0.113.88",
            "src_port": 41234,
            "dst_ip": "172.16.0.4",
            "dst_port": 22,
            "protocol": "TCP",
        },
    ]
    import json
    payload_bytes = json.dumps(json_data).encode("utf-8")

    files = {"file": ("fw_stream.json", io.BytesIO(payload_bytes), "application/json")}
    response = client.post("/api/v1/ingestion/upload", files=files, data={"parser_type": "firewall"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["events_processed"] == 2
    assert data["events_failed"] == 0


def test_import_with_malformed_records(client: TestClient):
    """Verifies that malformed rows are quarantined into rejected_records without crashing."""
    csv_data = (
        "timestamp,user,action,source_ip\n"
        "2026-10-27T11:00:00Z,validuser,login_success,10.0.0.1\n"
        "not_a_timestamp,baduser,login_failed,10.0.0.2\n"  # Invalid timestamp
        "2026-10-27T11:02:00Z,badipuser,login_failed,999.999.999.999\n"  # Invalid IP
        "2026-10-27T11:03:00Z,validuser2,login_success,10.0.0.3\n"
    )

    files = {"file": ("mixed_auth.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/ingestion/upload", files=files, data={"parser_type": "auth"})

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partially_failed"
    assert data["events_processed"] == 2
    assert data["events_failed"] == 2
    assert len(data["rejected_summary"]) == 2

    # Verify detailed rejections in job details
    job_id = data["job_id"]
    job_res = client.get(f"/api/v1/ingestion/jobs/{job_id}")
    assert job_res.status_code == 200
    job_data = job_res.json()
    assert job_data["events_failed"] == 2
    reasons = [r["reason"] for r in job_data["rejected_records"]]
    assert any("Timestamp validation failed" in r for r in reasons)
    assert any("Invalid IP address" in r for r in reasons)


def test_duplicate_batch_idempotency(client: TestClient):
    """Verifies that submitting the exact same file twice is detected and handled idempotently."""
    csv_data = (
        "timestamp,user,action,source_ip\n"
        "2026-10-27T12:00:00Z,idemp_user,login_success,10.0.5.5\n"
    )
    content = csv_data.encode("utf-8")

    # First submission
    files1 = {"file": ("idempotent_test.csv", io.BytesIO(content), "text/csv")}
    res1 = client.post("/api/v1/ingestion/upload", files=files1, data={"parser_type": "auth"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["events_processed"] == 1
    assert data1["is_duplicate_batch"] is False

    # Second submission with identical bytes
    files2 = {"file": ("idempotent_test.csv", io.BytesIO(content), "text/csv")}
    res2 = client.post("/api/v1/ingestion/upload", files=files2, data={"parser_type": "auth"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_duplicate_batch"] is True
    assert "Duplicate batch detected" in data2["message"]


def test_empty_file_rejected(client: TestClient):
    """Verifies that an empty file upload is rejected with HTTP 400."""
    files = {"file": ("empty.csv", io.BytesIO(b""), "text/csv")}
    response = client.post("/api/v1/ingestion/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_disallowed_extension_rejected(client: TestClient):
    """Verifies that unauthorized file extensions (.exe) are rejected."""
    files = {"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/octet-stream")}
    response = client.post("/api/v1/ingestion/upload", files=files)
    assert response.status_code == 400
    assert "unsupported file extension" in response.json()["detail"].lower()


def test_oversized_upload_limit(client: TestClient, monkeypatch):
    """Verifies that files exceeding configured byte limits are rejected with HTTP 413."""
    from app.config import settings
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 50)  # Low limit for testing

    files = {"file": ("oversized.csv", io.BytesIO(b"a" * 100), "text/csv")}
    response = client.post("/api/v1/ingestion/upload", files=files)
    assert response.status_code == 413
    assert "exceeds maximum upload size" in response.json()["detail"].lower()


def test_credential_sanitization(client: TestClient):
    """Verifies that sensitive password tokens in raw logs are redacted."""
    csv_data = (
        "timestamp,user,action,source_ip,password\n"
        "2026-10-27T13:00:00Z,analyst,login_attempt,10.0.1.1,SuperSecretPassword123!\n"
    )
    files = {"file": ("passwords.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    response = client.post("/api/v1/ingestion/upload", files=files, data={"parser_type": "auth"})
    assert response.status_code == 200

    # Query the ingested event and inspect raw_payload
    events = client.get("/api/v1/events?search=analyst").json()
    assert events["total_count"] >= 1
    event = events["items"][0]
    assert "SuperSecretPassword123!" not in event["raw_payload"]
    assert "[REDACTED]" in event["raw_payload"]


def test_log_source_management_endpoints(client: TestClient):
    """Verifies creating and querying log sources."""
    create_payload = {
        "name": "Edge-Firewall-Corp",
        "source_type": "suricata_nids",
        "description": "Perimeter NIDS collector",
        "ip_address": "192.168.100.1",
        "retention_days": 180,
    }
    create_res = client.post("/api/v1/sources", json=create_payload)
    assert create_res.status_code == 201
    source_id = create_res.json()["id"]

    list_res = client.get("/api/v1/sources")
    assert list_res.status_code == 200
    sources = list_res.json()
    assert any(s["name"] == "Edge-Firewall-Corp" for s in sources["items"])

    get_res = client.get(f"/api/v1/sources/{source_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Edge-Firewall-Corp"
