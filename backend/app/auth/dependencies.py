"""Authentication and Role-Based Access Control (RBAC) dependencies."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)


def get_current_user(
    db: Session = Depends(get_db),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role"),
) -> User:
    """Resolves requesting user identity and role from headers with safe development fallback.

    Allows automated tests and clients to test multiple RBAC tiers via headers:
    - X-User-Id: UUID or username of user in database
    - X-User-Role: Specific role for dynamic test user provisioning
    """
    user: Optional[User] = None

    # 1. Lookup by ID or username if header supplied
    if x_user_id:
        try:
            val_uuid = UUID(x_user_id)
            user = db.query(User).filter(User.id == val_uuid).first()
        except (ValueError, AttributeError):
            user = db.query(User).filter(User.username == x_user_id).first()

    # 2. Lookup or provision user matching X-User-Role if requested
    if not user and x_user_role:
        try:
            role_enum = UserRole(x_user_role.lower())
            user = (
                db.query(User)
                .filter(User.role == role_enum, User.status == UserStatus.ACTIVE)
                .first()
            )
            if not user:
                # Provision dynamic test user for requested role
                user = User(
                    username=f"analyst_{role_enum.value}",
                    email=f"{role_enum.value}@sentinel.local",
                    full_name=f"SOC {role_enum.value.replace('_', ' ').title()}",
                    hashed_password="mock_hashed_secret",
                    role=role_enum,
                    status=UserStatus.ACTIVE,
                )
                db.add(user)
                db.commit()
                db.refresh(user)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role '{x_user_role}'.",
            )

    # 3. Default fallback for development/demo: active Incident Responder
    if not user:
        user = (
            db.query(User)
            .filter(User.username == "lead_responder")
            .first()
        )
        if not user:
            user = User(
                username="lead_responder",
                email="lead_responder@sentinel.local",
                full_name="Lead Incident Responder",
                hashed_password="mock_hashed_secret",
                role=UserRole.INCIDENT_RESPONDER,
                status=UserStatus.ACTIVE,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    # 4. Check active account status
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User account is {user.status.value}.",
        )

    return user


def require_roles(allowed_roles: List[UserRole]):
    """Enforces that the current authenticated user belongs to an approved RBAC tier."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            role_names = ", ".join(r.value for r in allowed_roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Insufficient permissions: Role '{current_user.role.value}' lacks authority. "
                    f"Requires one of: [{role_names}]."
                ),
            )
        return current_user

    return role_checker
