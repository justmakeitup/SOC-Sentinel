"""Pydantic schemas for SOC security reporting and analytics."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class TimeSeriesPoint(BaseModel):
    timestamp: str = Field(..., description="Date or hour bucket label (UTC ISO/YYYY-MM-DD)")
    count: int = Field(..., ge=0, description="Total aggregated event occurrences")


class RuleAlertCount(BaseModel):
    rule_code: str
    rule_name: str
    severity: str
    count: int = Field(..., ge=0)


class IncidentStatusMetric(BaseModel):
    status: str
    count: int = Field(..., ge=0)


class MTTRMetric(BaseModel):
    mean_time_to_resolve_minutes: Optional[float] = Field(
        None, description="Average duration in minutes from incident creation to resolution"
    )
    mean_time_to_resolve_hours: Optional[float] = Field(
        None, description="Average duration in hours from incident creation to resolution"
    )
    resolved_incidents_count: int = Field(
        ..., description="Number of resolved/closed cases used to calculate MTTR"
    )
    sample_description: str = Field(
        ..., description="Sample size context or reason if insufficient data exists"
    )


class TopAttackerIP(BaseModel):
    ip: str
    event_count: int
    alert_count: int


class OperationalReportResponse(BaseModel):
    """Aggregated operational report computed from real database telemetry within a date range."""
    model_config = ConfigDict(from_attributes=True)

    start_date: str
    end_date: str
    event_category_filter: Optional[str] = None
    log_source_filter: Optional[str] = None

    total_events: int
    total_alerts: int
    total_incidents: int

    event_volume_timeseries: List[TimeSeriesPoint]
    alerts_by_severity: Dict[str, int]
    alerts_by_rule: List[RuleAlertCount]
    incidents_by_status: Dict[str, int]
    mttr_metrics: MTTRMetric
    top_source_ips: List[TopAttackerIP]

    metric_definitions: Dict[str, str] = Field(
        default_factory=dict,
        description="Transparent documentation of SQL formulas and metric calculation rules",
    )
    generated_at: datetime
