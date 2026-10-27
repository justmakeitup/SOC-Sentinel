"""Pydantic validation schemas for SOC dashboard summary and metrics."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class TimeSeriesPoint(BaseModel):
    """Data point representing security event volume within a time slice."""
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp or bucket label")
    count: int = Field(default=0, ge=0)


class DashboardSummaryResponse(BaseModel):
    """Aggregated operational metrics for executive and analyst overview."""
    events_processed: int = Field(default=0, ge=0)
    active_alerts: int = Field(default=0, ge=0)
    open_incidents: int = Field(default=0, ge=0)
    critical_alerts: int = Field(default=0, ge=0)
    event_volume_timeseries: List[TimeSeriesPoint] = Field(default_factory=list)
    severity_distribution: Dict[str, int] = Field(
        default_factory=lambda: {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "informational": 0,
        }
    )
    last_updated: Optional[str] = None
