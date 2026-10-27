"""Comprehensive security test suite for Sentinel SOC platform.

Validates:
- Unauthenticated request rejection (401 Unauthorized)
- Secure password hashing and enterprise complexity enforcement
- Login flow, brute-force lockout, and JWT token issuance
- Token verification via Bearer header and HttpOnly cookies
- Privilege escalation prevention (users cannot assign themselves admin role)
- Server-side RBAC enforcement on sensitive endpoints (ingestion, rules, audit, users)
- Non-repudiation audit logging for administrative actions
- Defensive HTTP security headers
- Error masking (preventing stack trace or internal leakage)
"""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    hash_password,
    validate_password_complexity,
    verify_password,
)
from app.models.audit import AuditEvent
from app.models.user import User, UserRole, UserStatus


@pytest.fixture
def test_admin_user(db_session: Session) -> User:
    user = User(
        username="sec_admin",
        email="sec_admin@sentinel.org",
        full_name="Security Admin",
        hashed_password=hash_password("AdminSecret!2026#"),
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_analyst_user(db_session: Session) -> User:
    user = User(
        username="triage_user",
        email="triage_user@sentinel.org",
        full_name="Triage Analyst",
        hashed_password=hash_password("AnalystSecret!2026#"),
        role=UserRole.ANALYST_TIER_1,
        status=UserStatus.ACTIVE,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# --------------------------------------------------------------------------
# 1. Cryptographic Password Hashing & Complexity Policy
# --------------------------------------------------------------------------

def test_password_hashing_and_verification():
    raw_pass = "EnterpriseP@ssw0rd!2026"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False


def test_password_complexity_enforcement():
    # Valid
    validate_password_complexity("StrongP@ss123")

    # Too short (< 10)
    with pytest.raises(ValueError, match="at least 10 characters"):
        validate_password_complexity("Short1!")

    # No uppercase
    with pytest.raises(ValueError, match="uppercase"):
        validate_password_complexity("lowercase_only_123!")

    # No lowercase
    with pytest.raises(ValueError, match="lowercase"):
        validate_password_complexity("UPPERCASE_ONLY_123!")

    # No numeric digit
    with pytest.raises(ValueError, match="numeric"):
        validate_password_complexity("NoDigitsAllowedHere!")

    # No special character
    with pytest.raises(ValueError, match="special character"):
        validate_password_complexity("NoSpecialCharacter123")


# --------------------------------------------------------------------------
# 2. Authentication & Login Lifecycle Tests
# --------------------------------------------------------------------------

def test_login_success_username_and_cookie_generation(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "triage_user",
            "password": "AnalystSecret!2026#",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "triage_user"
    assert data["user"]["role"] == "analyst_tier_1"

    # Verify HttpOnly cookie was set
    assert "access_token" in resp.cookies
    cookie_header = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in cookie_header
    assert "samesite=lax" in cookie_header.lower()


def test_login_success_email(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "triage_user@sentinel.org",
            "password": "AnalystSecret!2026#",
        },
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_invalid_credentials_rejected(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={
            "username_or_email": "triage_user",
            "password": "BadPassword999!",
        },
    )
    assert resp.status_code == 401
    assert "Invalid authentication credentials" in resp.json()["detail"]


def test_brute_force_account_lockout(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
    db_session: Session,
):
    """Submitting 5 consecutive invalid credentials locks account and denies subsequent access."""
    for attempt in range(4):
        r = unauthenticated_client.post(
            "/api/v1/auth/login",
            json={"username_or_email": "triage_user", "password": f"WrongAttempt{attempt}!"},
        )
        assert r.status_code == 401

    # 5th attempt triggers lockout
    lock_resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "triage_user", "password": "WrongAttempt5!"},
    )
    assert lock_resp.status_code == 403
    assert "Account locked" in lock_resp.json()["detail"]

    # Verify database status updated to locked
    db_session.refresh(test_analyst_user)
    assert test_analyst_user.status == UserStatus.LOCKED

    # Even with correct password, locked account cannot authenticate
    correct_resp = unauthenticated_client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "triage_user", "password": "AnalystSecret!2026#"},
    )
    assert correct_resp.status_code == 403
    assert "locked" in correct_resp.json()["detail"]


# --------------------------------------------------------------------------
# 3. JWT Token Validation (Bearer Header & Cookie Extraction)
# --------------------------------------------------------------------------

def test_access_with_valid_bearer_token(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    token = create_access_token({
        "sub": str(test_analyst_user.id),
        "username": test_analyst_user.username,
        "role": test_analyst_user.role.value,
    })

    resp = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == "triage_user"


def test_access_with_valid_cookie(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    token = create_access_token({
        "sub": str(test_analyst_user.id),
        "username": test_analyst_user.username,
        "role": test_analyst_user.role.value,
    })

    unauthenticated_client.cookies.set("access_token", token)
    resp = unauthenticated_client.get("/api/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json()["username"] == "triage_user"


def test_expired_token_rejected(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    expired_token = create_access_token(
        {
            "sub": str(test_analyst_user.id),
            "username": test_analyst_user.username,
            "role": test_analyst_user.role.value,
        },
        expires_delta=timedelta(seconds=-10),  # expired 10s ago
    )

    resp = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


def test_tampered_token_rejected(
    unauthenticated_client: TestClient,
    test_analyst_user: User,
):
    token = create_access_token({
        "sub": str(test_analyst_user.id),
        "username": test_analyst_user.username,
        "role": test_analyst_user.role.value,
    })
    # Tamper with signature
    tampered = token[:-4] + "AAAA"

    resp = unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# 4. Unauthenticated Access Denial Tests
# --------------------------------------------------------------------------

@pytest.mark.parametrize("endpoint,method", [
    ("/api/v1/auth/me", "GET"),
    ("/api/v1/auth/logout", "POST"),
    ("/api/v1/auth/users", "GET"),
    ("/api/v1/auth/users", "POST"),
    ("/api/v1/audit", "GET"),
])
def test_unauthenticated_requests_denied(
    unauthenticated_client: TestClient,
    endpoint: str,
    method: str,
):
    if method == "GET":
        resp = unauthenticated_client.get(endpoint)
    else:
        resp = unauthenticated_client.post(endpoint, json={})
    assert resp.status_code == 401
    assert "Not authenticated" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 5. Privilege Escalation Prevention
# --------------------------------------------------------------------------

def test_self_registration_strictly_prohibits_admin_privilege(
    unauthenticated_client: TestClient,
    db_session: Session,
):
    """Users cannot self-assign administrator role; registration schema and endpoint force Tier 1."""
    resp = unauthenticated_client.post(
        "/api/v1/auth/register",
        json={
            "username": "attacker_attempt",
            "email": "attacker@darkweb.org",
            "full_name": "Hostile Actor",
            "password": "AttackerSecret!2026#",
            "role": "admin",  # Extra field or attempt to claim admin
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["role"] == "analyst_tier_1"

    db_user = db_session.query(User).filter(User.username == "attacker_attempt").first()
    assert db_user.role == UserRole.ANALYST_TIER_1


def test_analyst_cannot_provision_users(
    client: TestClient,
    test_analyst_user: User,
):
    """Tier 1 Analyst cannot call /api/v1/auth/users to provision accounts."""
    resp = client.post(
        "/api/v1/auth/users",
        headers={"X-User-Id": str(test_analyst_user.id)},
        json={
            "username": "rogue_admin",
            "email": "rogue@sentinel.org",
            "full_name": "Rogue Admin",
            "password": "RoguePassword!2026#",
            "role": "admin",
        },
    )
    assert resp.status_code == 403
    assert "Insufficient permissions" in resp.json()["detail"]


def test_admin_can_provision_custom_roles(
    client: TestClient,
    test_admin_user: User,
    db_session: Session,
):
    """Administrator can provision elevated roles (Responder, Engineer, Admin)."""
    resp = client.post(
        "/api/v1/auth/users",
        headers={"X-User-Id": str(test_admin_user.id)},
        json={
            "username": "provisioned_responder",
            "email": "responder@sentinel.org",
            "full_name": "Authorized Responder",
            "password": "ProvisionedSecret!2026#",
            "role": "incident_responder",
            "status": "active",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["role"] == "incident_responder"

    # Verify audit event recorded
    audit = db_session.query(AuditEvent).filter(
        AuditEvent.action == "user_provisioned_by_admin"
    ).first()
    assert audit is not None
    assert audit.actor_id == test_admin_user.id


def test_admin_cannot_demote_or_suspend_themselves(
    client: TestClient,
    test_admin_user: User,
):
    """Protects against accidental self-lockout by administrators."""
    # Attempt self-demotion
    demote_resp = client.patch(
        f"/api/v1/auth/users/{test_admin_user.id}",
        headers={"X-User-Id": str(test_admin_user.id)},
        json={"role": "analyst_tier_1"},
    )
    assert demote_resp.status_code == 400
    assert "demote their own" in demote_resp.json()["detail"]

    # Attempt self-suspension
    suspend_resp = client.patch(
        f"/api/v1/auth/users/{test_admin_user.id}",
        headers={"X-User-Id": str(test_admin_user.id)},
        json={"status": "suspended"},
    )
    assert suspend_resp.status_code == 400
    assert "suspend or lock their own" in suspend_resp.json()["detail"]


# --------------------------------------------------------------------------
# 6. Sensitive Operations RBAC Enforcement
# --------------------------------------------------------------------------

def test_tier1_analyst_prohibited_from_tuning_detection_rules(
    client: TestClient,
    test_analyst_user: User,
):
    resp = client.patch(
        "/api/v1/rules/SEC-AUTH-001",
        headers={"X-User-Id": str(test_analyst_user.id)},
        json={"threshold_count": 20},
    )
    assert resp.status_code == 403
    assert "Insufficient permissions" in resp.json()["detail"]


def test_tier1_analyst_prohibited_from_replaying_rules(
    client: TestClient,
    test_analyst_user: User,
):
    resp = client.post(
        "/api/v1/rules/replay",
        headers={"X-User-Id": str(test_analyst_user.id)},
        json={
            "start_time": "2026-03-01T00:00:00Z",
            "end_time": "2026-03-02T00:00:00Z",
        },
    )
    assert resp.status_code == 403


def test_tier1_analyst_prohibited_from_reading_audit_trail(
    client: TestClient,
    test_analyst_user: User,
):
    resp = client.get(
        "/api/v1/audit",
        headers={"X-User-Id": str(test_analyst_user.id)},
    )
    assert resp.status_code == 403


# --------------------------------------------------------------------------
# 7. Defensive HTTP Security Headers
# --------------------------------------------------------------------------

def test_security_headers_present_on_all_responses(client: TestClient):
    resp = client.get("/")
    assert resp.status_code == 200
    headers = resp.headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert "1; mode=block" in headers["x-xss-protection"]
    assert "strict-origin-when-cross-origin" in headers["referrer-policy"]


# --------------------------------------------------------------------------
# 8. Error Sanitization & Masking
# --------------------------------------------------------------------------

def test_error_envelope_sanitization_no_stack_traces(client: TestClient):
    # Non-existent endpoint (404)
    resp404 = client.get("/api/v1/non_existent_route_1234")
    assert resp404.status_code == 404

    # Invalid UUID parameter (422)
    resp422 = client.get("/api/v1/alerts/not-a-valid-uuid")
    assert resp422.status_code == 422
    data = resp422.json()
    assert data["error"] is True
    assert "errors" in data
    # Ensure no internal filesystem paths or Python tracebacks are leaked
    body_str = resp422.text
    assert "Traceback" not in body_str
    assert "site-packages" not in body_str
