"""Common schema definitions for responses, errors, pagination, and health status."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class SubsystemHealth(BaseModel):
    """Health metrics for an individual platform subsystem."""
    status: str = Field(..., description="Operational status: healthy, degraded, disconnected")
    latency_ms: Optional[float] = Field(default=None, description="Subsystem round-trip latency in milliseconds")
    error: Optional[str] = Field(default=None, description="Detailed diagnostic error message if unhealthy")


class HealthResponse(BaseModel):
    """Comprehensive system health and readiness payload."""
    status: str = Field(default="healthy", description="Aggregate platform status")
    environment: str = Field(..., description="Active operating environment")
    version: str = Field(..., description="Deployed Sentinel software version")
    timestamp: datetime = Field(..., description="UTC server timestamp")
    subsystems: dict[str, SubsystemHealth] = Field(
        ...,
        description="Health states of backing services including database and event pipeline",
    )


class PaginationParams(BaseModel):
    """Standardized query parameters for paginated list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number starting at 1")
    page_size: int = Field(default=50, ge=1, le=500, description="Records per page (max 500)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated entity collections."""
    model_config = ConfigDict(from_attributes=True)

    items: List[T]
    total_count: int
    page: int
    page_size: int
    total_pages: int
