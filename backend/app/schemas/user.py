"""Pydantic validation schemas for user management and authentication."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.security import validate_password_complexity
from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    full_name: str = Field(..., min_length=1, max_length=128)
    role: UserRole = UserRole.ANALYST_TIER_1


class UserCreate(UserBase):
    password: str = Field(..., min_length=10, description="Plaintext password satisfying SOC complexity policy")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_complexity(v)
        return v


class UserRegistration(BaseModel):
    """Public registration request. Users cannot assign roles to themselves; role defaults to Tier-1 Analyst."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    full_name: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=10, description="Plaintext password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_complexity(v)
        return v


class UserAdminCreate(BaseModel):
    """Administrator-only user creation schema allowing arbitrary RBAC role provisioning."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64, pattern=r"^[a-zA-Z0-9_\-\.]+$")
    full_name: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=10)
    role: UserRole = UserRole.ANALYST_TIER_1
    status: UserStatus = UserStatus.ACTIVE

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_complexity(v)
        return v


class UserAdminUpdate(BaseModel):
    """Administrator-only update for modifying user roles and account operational states."""
    full_name: Optional[str] = Field(None, min_length=1, max_length=128)
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None


class LoginRequest(BaseModel):
    """Credentials submitted for authentication."""
    username_or_email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: UserStatus
    is_mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT Bearer token and user profile returned upon successful authentication."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user: UserRead
