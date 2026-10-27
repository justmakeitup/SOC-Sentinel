"""API v1 Router aggregation."""

from app.api.v1.endpoints import alerts, dashboard, health, incidents
from fastapi import APIRouter

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(dashboard.router)
api_v1_router.include_router(alerts.router)
api_v1_router.include_router(incidents.router)
