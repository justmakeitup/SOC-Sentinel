"""Authentication and Role-Based Access Control (RBAC) dependencies."""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole, UserStatus

logger = logging.getLogger(__name__)


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(default=None),
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role"),
    x_anonymous: Optional[str] = Header(default=None, alias="X-Anonymous"),
) -> User:
    """Authenticates the requesting user identity and role.

    Resolution order:
    1. Authorization: Bearer <jwt_token> header.
    2. Secure HttpOnly cookie: access_token.
    3. In non-production environments (development/testing):
       - Explicit X-Anonymous: true header blocks mock resolution to test unauthenticated access.
       - X-User-Id: UUID or username of user in database.
       - X-User-Role: Specific role for dynamic test user provisioning.
    4. If none of the above are valid, raises HTTP 401 Unauthorized.
    """
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    elif access_token_cookie:
        token = access_token_cookie.strip()

    # 1. Validate JWT Token if provided
    if token:
        try:
            payload = decode_access_token(token)
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload: missing subject identifier.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            user = db.query(User).filter(User.id == UUID(user_id_str)).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account matching token does not exist.",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: User account is {user.status.value}.",
                )
            return user
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication token validation failed: {str(exc)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # If explicit anonymous simulation header sent (and no token provided)
    if x_anonymous and x_anonymous.lower() in ("true", "1", "yes"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Provide a valid Bearer token or session cookie.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Non-production test & developer header resolution
    if settings.ENVIRONMENT != "production":
        user: Optional[User] = None

        if x_user_id:
            try:
                val_uuid = UUID(x_user_id)
                user = db.query(User).filter(User.id == val_uuid).first()
            except (ValueError, AttributeError):
                user = db.query(User).filter(User.username == x_user_id).first()

        if not user and x_user_role:
            try:
                role_enum = UserRole(x_user_role.lower())
                user = (
                    db.query(User)
                    .filter(User.role == role_enum, User.status == UserStatus.ACTIVE)
                    .first()
                )
                if not user:
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

        if user:
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: User account is {user.status.value}.",
                )
            return user

    # 3. Unauthenticated request rejection
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Provide a valid Bearer token or session cookie.",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
