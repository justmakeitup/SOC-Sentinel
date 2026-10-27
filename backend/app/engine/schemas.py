"""Pydantic schemas for detection rules, evaluation triggers, and replay execution."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertStatus
from app.models.rule import RuleSeverity, RuleType


class DetectionRuleDetailResponse(BaseModel):
    """Full detail of a detection rule including operational assumptions and MITRE mapping."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_code: str
    name: str
    description: str
    severity: RuleSeverity
    rule_type: RuleType
    is_active: bool
    time_window_seconds: int
    threshold_count: int
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    remediation_guidance: Optional[str] = None
    assumptions: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    expected_false_positives: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class DetectionRuleUpdateRequest(BaseModel):
    """Tunable rule configuration parameters."""

    is_active: Optional[bool] = None
    threshold_count: Optional[int] = Field(default=None, ge=1, le=1000)
    time_window_seconds: Optional[int] = Field(default=None, ge=1, le=86400)
    severity: Optional[RuleSeverity] = None


class ReplayRequest(BaseModel):
    """Specification for replaying telemetry through the detection engine."""

    start_time: datetime
    end_time: datetime


class ReplayResponse(BaseModel):
    """Results of replaying an event window."""

    start_time: str
    end_time: str
    events_evaluated: int
    alerts_generated_or_updated: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class AlertStatusUpdateRequest(BaseModel):
    """Schema for updating alert triage disposition."""

    status: AlertStatus


class AlertDetailResponse(BaseModel):
    """Complete alert record with supporting evidence and normalized events."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_id: UUID
    rule_code: Optional[str] = None
    rule_name: Optional[str] = None
    title: str
    description: str
    severity: RuleSeverity
    status: AlertStatus
    deduplication_key: str
    event_count: int
    context_data: Dict[str, Any] = Field(default_factory=dict)
    assigned_to_id: Optional[UUID] = None
    incident_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    supporting_events: List[Dict[str, Any]] = Field(default_factory=list)
