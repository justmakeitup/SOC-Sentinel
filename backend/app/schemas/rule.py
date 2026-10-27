"""Pydantic validation schemas for detection engineering rules."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.rule import RuleSeverity, RuleType


class DetectionRuleBase(BaseModel):
    rule_code: str = Field(..., max_length=32, description="Unique code e.g. 'RULE-AUTH-001'")
    name: str = Field(..., max_length=150)
    description: str
    severity: RuleSeverity = RuleSeverity.MEDIUM
    rule_type: RuleType = RuleType.THRESHOLD
    is_active: bool = True
    time_window_seconds: int = Field(default=300, ge=10, le=86400)
    threshold_count: int = Field(default=1, ge=1)
    mitre_tactic: Optional[str] = None
    mitre_technique: Optional[str] = None
    rule_logic: dict
    remediation_guidance: Optional[str] = None


class DetectionRuleCreate(DetectionRuleBase):
    pass


class DetectionRuleRead(DetectionRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version: int
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
