"""Pydantic validation schemas for user management and authentication."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=64)
    full_name: str = Field(..., min_length=1, max_length=128)
    role: UserRole = UserRole.ANALYST_TIER_1


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Plaintext password for account creation")


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: UserStatus
    is_mfa_enabled: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
