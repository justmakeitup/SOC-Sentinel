"""Normalization logic converting parsed records into unified ECS security events."""

import hashlib
import ipaddress
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError

from app.ingestion.parsers.base import RawRecord, RejectedRecord
from app.ingestion.sanitizer import sanitize_dict_fields, sanitize_raw_payload
from app.models.event import EventSeverity

# Standard timestamp formats to test sequentially
TIMESTAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S.%f%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%fZ",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%b %d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
]


class NormalizedEventSchema(BaseModel):
    """Internal Pydantic schema strictly validating normalized record constraints."""
    log_source_id: UUID
    timestamp: datetime
    event_type: str = Field(..., min_length=2, max_length=64)
    event_action: str = Field(..., min_length=2, max_length=64)
    severity: EventSeverity = EventSeverity.INFORMATIONAL
    source_ip: Optional[str] = None
    source_port: Optional[int] = Field(default=None, ge=1, le=65535)
    destination_ip: Optional[str] = None
    destination_port: Optional[int] = Field(default=None, ge=1, le=65535)
    protocol: Optional[str] = Field(default=None, max_length=16)
    user_name: Optional[str] = Field(default=None, max_length=128)
    host_name: Optional[str] = Field(default=None, max_length=255)
    process_name: Optional[str] = Field(default=None, max_length=255)
    process_path: Optional[str] = Field(default=None, max_length=512)
    command_line: Optional[str] = None
    raw_payload: str
    event_hash: str
    extra_fields: Optional[Dict[str, Any]] = None


def parse_timestamp(value: Any) -> datetime:
    """Robustly parses diverse timestamp formats into a UTC-aware datetime."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    if isinstance(value, (int, float)):
        # Handle UNIX epochs in seconds or milliseconds
        if value > 1e11:
            value = value / 1000.0
        return datetime.fromtimestamp(value, tz=timezone.utc)

    if not isinstance(value, str):
        raise ValueError(f"Unrecognized timestamp data type: {type(value)}")

    val_str = value.strip()
    if not val_str:
        raise ValueError("Timestamp value is empty")

    # Try ISO-8601 built-in first
    try:
        dt = datetime.fromisoformat(val_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    # Try explicit format patterns
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(val_str, fmt)
            if "%Y" not in fmt:
                dt = dt.replace(year=datetime.now(timezone.utc).year)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse timestamp: '{val_str}'")


def validate_ip(ip_val: Optional[Any]) -> Optional[str]:
    """Validates IPv4 or IPv6 address strings."""
    if not ip_val:
        return None
    val_str = str(ip_val).strip()
    if not val_str or val_str.lower() in ("-", "none", "null", "n/a"):
        return None
    try:
        ip_obj = ipaddress.ip_address(val_str)
        return str(ip_obj)
    except ValueError:
        raise ValueError(f"Invalid IP address format: '{val_str}'")


def validate_port(port_val: Optional[Any]) -> Optional[int]:
    """Validates network port integers in range 1-65535."""
    if port_val is None or port_val == "" or str(port_val).strip().lower() in ("-", "none", "null"):
        return None
    try:
        p = int(port_val)
        if 1 <= p <= 65535:
            return p
        raise ValueError(f"Port number {p} out of range 1-65535")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid port value: '{port_val}'")


def calculate_event_hash(source_id: UUID, event_time: datetime, payload: str) -> str:
    """Calculates cryptographic SHA-256 fingerprint guaranteeing idempotency."""
    raw_key = f"{source_id}:{event_time.isoformat()}:{payload}"
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


class EventNormalizer:
    """Harmonizes raw parsed records into NormalizedEventSchema instances."""

    def normalize(
        self,
        raw_record: RawRecord,
        log_source_id: UUID,
        parser_type: str = "generic",
    ) -> Tuple[Optional[NormalizedEventSchema], Optional[RejectedRecord]]:
        """Converts raw record dictionary to a normalized schema instance.

        Returns (NormalizedEventSchema, None) on success, or (None, RejectedRecord) on validation failure.
        """
        data = raw_record.data

        # 1. Resolve timestamp
        ts_val = (
            data.get("timestamp")
            or data.get("@timestamp")
            or data.get("time")
            or data.get("event_time")
            or data.get("datetime")
            or data.get("date")
        )
        if not ts_val:
            return None, RejectedRecord(
                line_number=raw_record.line_number,
                reason="Missing required timestamp field",
                raw_snippet=raw_record.raw_text,
            )

        try:
            event_timestamp = parse_timestamp(ts_val)
        except ValueError as exc:
            return None, RejectedRecord(
                line_number=raw_record.line_number,
                reason=f"Timestamp validation failed: {exc}",
                raw_snippet=raw_record.raw_text,
            )

        # 2. Resolve IPs and Ports with validation
        try:
            source_ip = validate_ip(
                data.get("source_ip")
                or data.get("src_ip")
                or data.get("client_ip")
                or data.get("ip")
            )
            destination_ip = validate_ip(
                data.get("destination_ip")
                or data.get("dst_ip")
                or data.get("target_ip")
            )
        except ValueError as exc:
            return None, RejectedRecord(
                line_number=raw_record.line_number,
                reason=str(exc),
                raw_snippet=raw_record.raw_text,
            )

        try:
            source_port = validate_port(data.get("source_port") or data.get("src_port"))
            destination_port = validate_port(data.get("destination_port") or data.get("dst_port"))
        except ValueError as exc:
            return None, RejectedRecord(
                line_number=raw_record.line_number,
                reason=str(exc),
                raw_snippet=raw_record.raw_text,
            )

        # 3. Protocol
        proto = data.get("protocol") or data.get("proto")
        protocol_str = str(proto).upper()[:16] if proto else None

        # 4. Identity & Host
        user_name = (
            data.get("user_name")
            or data.get("username")
            or data.get("user")
            or data.get("account")
        )
        if user_name:
            user_name = str(user_name).strip()[:128]

        host_name = data.get("host_name") or data.get("hostname") or data.get("host")
        if host_name:
            host_name = str(host_name).strip()[:255]

        # 5. Process execution
        process_name = data.get("process_name") or data.get("process") or data.get("app")
        if process_name:
            process_name = str(process_name).strip()[:255]

        command_line = data.get("command_line") or data.get("cmd") or data.get("command")
        if command_line:
            command_line = sanitize_raw_payload(str(command_line))

        # 6. Action and Event Type resolution based on parser type
        action_raw = str(
            data.get("event_action")
            or data.get("action")
            or data.get("outcome")
            or data.get("status")
            or "observed"
        ).lower().strip()

        event_type_raw = str(
            data.get("event_type")
            or data.get("category")
            or data.get("type")
            or ""
        ).lower().strip()

        # Taxonomy normalization heuristics
        if parser_type == "auth" or "login" in action_raw or "auth" in event_type_raw:
            event_type = "authentication"
            if any(term in action_raw for term in ("fail", "invalid", "bad", "denied")):
                event_action = "login_failed"
                severity = EventSeverity.MEDIUM
            elif any(term in action_raw for term in ("lock", "block", "freeze")):
                event_action = "account_locked"
                severity = EventSeverity.HIGH
            else:
                event_action = "login_success"
                severity = EventSeverity.INFORMATIONAL
        elif parser_type == "firewall" or any(term in action_raw for term in ("allow", "block", "drop", "deny", "permit")):
            event_type = "network_flow"
            if any(term in action_raw for term in ("block", "drop", "deny", "reject")):
                event_action = "connection_blocked"
                severity = EventSeverity.LOW
            else:
                event_action = "connection_allowed"
                severity = EventSeverity.INFORMATIONAL
        else:
            event_type = event_type_raw or "generic_telemetry"
            event_action = action_raw or "log_recorded"
            severity = EventSeverity.INFORMATIONAL

        # Override severity if explicitly supplied in record
        raw_sev = str(data.get("severity") or "").lower().strip()
        if raw_sev in ("critical", "high", "medium", "low", "informational"):
            severity = EventSeverity(raw_sev)

        # 7. Raw payload and sensitive data sanitization
        clean_raw_payload = sanitize_raw_payload(raw_record.raw_text)
        clean_extra_fields = sanitize_dict_fields(dict(data))

        # 8. Cryptographic deduplication hash
        event_hash = calculate_event_hash(log_source_id, event_timestamp, clean_raw_payload)

        try:
            schema = NormalizedEventSchema(
                log_source_id=log_source_id,
                timestamp=event_timestamp,
                event_type=event_type[:64],
                event_action=event_action[:64],
                severity=severity,
                source_ip=source_ip,
                source_port=source_port,
                destination_ip=destination_ip,
                destination_port=destination_port,
                protocol=protocol_str,
                user_name=user_name,
                host_name=host_name,
                process_name=process_name,
                command_line=command_line,
                raw_payload=clean_raw_payload,
                event_hash=event_hash,
                extra_fields=clean_extra_fields,
            )
            return schema, None
        except ValidationError as v_err:
            return None, RejectedRecord(
                line_number=raw_record.line_number,
                reason=f"Schema validation failed: {v_err}",
                raw_snippet=raw_record.raw_text,
            )
