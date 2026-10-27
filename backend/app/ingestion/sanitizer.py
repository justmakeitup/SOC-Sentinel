"""Sensitive data redaction utilities for log ingestion.

Prevents credentials, authorization tokens, passwords, and private keys
from being persisted in raw_payload, error logs, or rejected record summaries.
"""

import re
from typing import Any, Dict, List

# Keywords indicating sensitive field keys
SENSITIVE_KEY_PATTERNS = re.compile(
    r"(password|passwd|pwd|secret|token|api_key|access_token|authorization|auth_key|private_key|session_id|cookie)",
    re.IGNORECASE,
)

# Regex pattern for in-line key-value pairs (e.g. password=1234, "password": "xyz")
INLINE_SECRET_PATTERN = re.compile(
    r"""(?i)(password|passwd|pwd|secret|token|api_key|access_token|authorization)\s*[:=]\s*(['"][^'"]*['"]|\S+)"""
)


def is_sensitive_key(key: str) -> bool:
    """Returns True if the key name indicates sensitive credential data."""
    return bool(SENSITIVE_KEY_PATTERNS.search(key))


def sanitize_raw_payload(payload: str) -> str:
    """Replaces inline password or token values in raw text strings."""
    if not payload:
        return ""
    return INLINE_SECRET_PATTERN.sub(r"\1=[REDACTED]", payload)


def sanitize_csv_row(header: List[str], row: List[str]) -> str:
    """Constructs sanitized CSV string redacting any columns whose header is sensitive."""
    sanitized_cells = []
    for idx, cell in enumerate(row):
        col_name = header[idx] if idx < len(header) else ""
        if is_sensitive_key(col_name):
            sanitized_cells.append("[REDACTED]")
        else:
            sanitized_cells.append(sanitize_raw_payload(cell))
    return ",".join(sanitized_cells)


def sanitize_dict_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively redacts sensitive values from dictionaries."""
    sanitized: Dict[str, Any] = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_fields(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict_fields(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, str):
            sanitized[key] = sanitize_raw_payload(value)
        else:
            sanitized[key] = value
    return sanitized
