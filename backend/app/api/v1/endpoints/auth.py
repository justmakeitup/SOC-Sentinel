"""Authentication, session token management, and user administration endpoints."""

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_roles
from app.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    UserAdminCreate,
    UserAdminUpdate,
    UserRead,
    UserRegistration,
)
from app.services.audit_service import record_audit_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Access Control"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate analyst credentials and issue signed JWT session token",
)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """Verifies credentials, applies account lockout policy, and generates secure access tokens.

    Sets both:
    1. HTTP response body with Bearer JWT token.
    2. Secure, HttpOnly SameSite cookie for browser-based session continuity.
    """
    identifier = payload.username_or_email.strip()
    client_ip = request.client.host if request.client else "unknown"

    user = (
        db.query(User)
        .filter(or_(User.username == identifier, User.email == identifier.lower()))
        .first()
    )

    if not user:
        record_audit_event(
            db,
            action="user_login_failed",
            entity_type="auth",
            entity_id=identifier,
            actor_id=None,
            actor_name="anonymous",
            actor_ip=client_ip,
            details={"reason": "User not found", "attempted_identifier": identifier},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check operational status (Lockout / Suspension)
    if user.status != UserStatus.ACTIVE:
        record_audit_event(
            db,
            action="user_login_blocked_status",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            actor_name=user.username,
            actor_ip=client_ip,
            details={"status": user.status.value},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Account is currently {user.status.value}. Contact SOC Administrator.",
        )

    # Verify password hash
    if not verify_password(payload.password, user.hashed_password):
        user.failed_login_attempts += 1

        # Brute force lockout threshold (5 consecutive failures)
        if user.failed_login_attempts >= 5:
            user.status = UserStatus.LOCKED
            db.commit()
            record_audit_event(
                db,
                action="user_account_locked",
                entity_type="user",
                entity_id=str(user.id),
                actor_id=user.id,
                actor_name=user.username,
                actor_ip=client_ip,
                details={"failed_attempts": user.failed_login_attempts, "action": "locked_account"},
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account locked due to 5 consecutive failed login attempts. Contact SOC administration.",
            )

        db.commit()
        record_audit_event(
            db,
            action="user_login_failed",
            entity_type="user",
            entity_id=str(user.id),
            actor_id=user.id,
            actor_name=user.username,
            actor_ip=client_ip,
            details={"failed_attempts": user.failed_login_attempts},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful Authentication: Reset failed attempts & update last login
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    record_audit_event(
        db,
        action="user_login_success",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
        actor_name=user.username,
        actor_ip=client_ip,
        details={"role": user.role.value},
    )

    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
    }
    access_token = create_access_token(token_data)
    expires_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Apply secure cookie settings
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=not settings.DEBUG,  # True in production HTTPS
        samesite="lax",
        max_age=expires_seconds,
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=expires_seconds,
        user=UserRead.model_validate(user),
    )


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Public analyst registration (Strictly restricted to Tier-1 role)",
)
def register(
    payload: UserRegistration,
    request: Request,
    db: Session = Depends(get_db),
) -> UserRead:
    """Provisions a new analyst account.

    Security Guarantee: Role manipulation is prohibited; new public self-registrations
    are strictly assigned Tier-1 Analyst privileges regardless of input payload.
    """
    client_ip = request.client.host if request.client else "unknown"

    existing_user = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.email.lower()))
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that username or email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        username=payload.username,
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hashed_pw,
        role=UserRole.ANALYST_TIER_1,  # Strictly Tier 1 for self-registration
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        action="user_registered",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=user.id,
        actor_name=user.username,
        actor_ip=client_ip,
        details={"role": user.role.value, "registration_type": "self_service"},
    )
    db.commit()

    return UserRead.model_validate(user)


@router.post(
    "/logout",
    summary="Invalidate active session and clear authentication cookies",
)
def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Clears session cookie and records audit event."""
    client_ip = request.client.host if request.client else "unknown"

    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        path="/",
    )

    record_audit_event(
        db,
        action="user_logout",
        entity_type="user",
        entity_id=str(current_user.id),
        actor_id=current_user.id,
        actor_name=current_user.username,
        actor_ip=client_ip,
        details={"role": current_user.role.value},
    )
    db.commit()

    return {"message": "Session invalidated successfully."}


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get authenticated analyst profile and active permissions",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Returns the verified profile and assigned RBAC role of the caller."""
    return UserRead.model_validate(current_user)


# --------------------------------------------------------------------------
# Administrative User Management (Restricted to Administrator Role)
# --------------------------------------------------------------------------

@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Provision user accounts with custom roles (Administrator only)",
)
def admin_create_user(
    payload: UserAdminCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> UserRead:
    """Allows administrators to provision users with elevated RBAC roles (Tier 2, Responder, Engineer, Admin)."""
    client_ip = request.client.host if request.client else "unknown"

    existing_user = (
        db.query(User)
        .filter(or_(User.username == payload.username, User.email == payload.email.lower()))
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that username or email address already exists.",
        )

    hashed_pw = hash_password(payload.password)
    user = User(
        username=payload.username,
        email=payload.email.lower(),
        full_name=payload.full_name,
        hashed_password=hashed_pw,
        role=payload.role,
        status=payload.status,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db,
        action="user_provisioned_by_admin",
        entity_type="user",
        entity_id=str(user.id),
        actor_id=admin_user.id,
        actor_name=admin_user.username,
        actor_ip=client_ip,
        details={
            "target_username": user.username,
            "target_role": user.role.value,
            "target_status": user.status.value,
        },
    )
    db.commit()

    return UserRead.model_validate(user)


@router.get(
    "/users",
    response_model=PaginatedResponse[UserRead],
    summary="List SOC user accounts (Administrator and SOC Manager)",
)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    role: Optional[UserRole] = Query(default=None),
    status_filter: Optional[UserStatus] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.SOC_MANAGER])),
) -> PaginatedResponse[UserRead]:
    """Retrieves directory of SOC operators and their assigned authorization tiers."""
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if status_filter:
        query = query.filter(User.status == status_filter)

    total_count = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return PaginatedResponse(
        items=[UserRead.model_validate(u) for u in users],
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserRead,
    summary="Update user role or operational status (Administrator only)",
)
def admin_update_user(
    user_id: UUID,
    payload: UserAdminUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_roles([UserRole.ADMIN])),
) -> UserRead:
    """Allows administrators to elevate/demote analyst roles or suspend/lock compromised accounts."""
    client_ip = request.client.host if request.client else "unknown"

    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' does not exist.",
        )

    # Protect against self-demotion or self-lockout of the last administrator
    if target_user.id == admin_user.id:
        if payload.status and payload.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot suspend or lock their own active account.",
            )
        if payload.role and payload.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Administrators cannot demote their own administrative role.",
            )

    changes = {}
    if payload.full_name is not None and payload.full_name != target_user.full_name:
        changes["full_name"] = {"old": target_user.full_name, "new": payload.full_name}
        target_user.full_name = payload.full_name

    if payload.role is not None and payload.role != target_user.role:
        changes["role"] = {"old": target_user.role.value, "new": payload.role.value}
        target_user.role = payload.role

    if payload.status is not None and payload.status != target_user.status:
        changes["status"] = {"old": target_user.status.value, "new": payload.status.value}
        target_user.status = payload.status

    if changes:
        record_audit_event(
            db,
            action="user_updated_by_admin",
            entity_type="user",
            entity_id=str(target_user.id),
            actor_id=admin_user.id,
            actor_name=admin_user.username,
            actor_ip=client_ip,
            details={"changes": changes, "target_username": target_user.username},
        )
    db.commit()
    db.refresh(target_user)

    return UserRead.model_validate(target_user)
