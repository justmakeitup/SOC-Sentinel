"""Cryptographic security utilities for password hashing, validation, and JWT session handling."""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.config import settings


class PasswordPolicyError(ValueError):
    """Raised when a proposed password fails SOC security complexity requirements."""
    pass


def validate_password_complexity(password: str) -> None:
    """Enforces enterprise SOC password complexity standards:
    - Minimum length 10 characters
    - At least one uppercase letter [A-Z]
    - At least one lowercase letter [a-z]
    - At least one numeric digit [0-9]
    - At least one special symbol [!@#$%^&*()_+\\-=\\[\\]{}|;:,.<>?]
    """
    if len(password) < 10:
        raise PasswordPolicyError("Password must be at least 10 characters in length.")
    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("Password must contain at least one uppercase letter [A-Z].")
    if not re.search(r"[a-z]", password):
        raise PasswordPolicyError("Password must contain at least one lowercase letter [a-z].")
    if not re.search(r"\d", password):
        raise PasswordPolicyError("Password must contain at least one numeric digit [0-9].")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?~`/\\]", password):
        raise PasswordPolicyError(
            "Password must contain at least one special character (e.g. !@#$%^&*)."
        )


def hash_password(password: str) -> str:
    """Hashes a plaintext password using bcrypt with work factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash using constant-time comparison."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Generates a cryptographically signed JWT access token containing user identity and role claims."""
    to_encode = data.copy()
    now_utc = datetime.now(timezone.utc)
    if expires_delta:
        expire = now_utc + expires_delta
    else:
        expire = now_utc + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now_utc,
        "nbf": now_utc,
    })
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates JWT signature, expiration, and required claims."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "role"]},
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Authentication token has expired. Please re-authenticate.")
    except jwt.InvalidTokenError as exc:
        raise ValueError(f"Invalid authentication token: {str(exc)}")
