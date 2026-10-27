"""API v1 Router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    alerts,
    audit,
    auth,
    dashboard,
    events,
    health,
    incidents,
    ingestion,
    reports,
    rules,
    sources,
)

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(audit.router)
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(alerts.router)
api_v1_router.include_router(incidents.router)
api_v1_router.include_router(ingestion.router)
api_v1_router.include_router(events.router)
api_v1_router.include_router(sources.router)
api_v1_router.include_router(rules.router)
api_v1_router.include_router(reports.router)
