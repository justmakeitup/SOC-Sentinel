"""FastAPI application entrypoint for Sentinel SOC Platform."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_v1_router
from app.config import settings
from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup and shutdown procedures."""
    setup_logging()
    logger.info("Initializing Sentinel Security Monitoring & Incident Response Platform")
    yield
    logger.info("Sentinel platform shutting down cleanly")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces essential defensive HTTP security headers to mitigate common web application threats."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Protects against Denial of Service (DoS) memory exhaustion by rejecting oversized request bodies."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length_int = int(content_length)
                # Max allowed upload limit plus 2MB buffer for multipart metadata
                max_bytes = settings.MAX_UPLOAD_SIZE_BYTES + (2 * 1024 * 1024)
                if length_int > max_bytes:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "error": True,
                            "status_code": 413,
                            "detail": f"Request body size exceeds configured maximum threshold of {max_bytes} bytes.",
                        },
                    )
            except ValueError:
                pass
        return await call_next(request)


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Security Monitoring & Incident Response Platform backend API.",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Defensive Middleware Chain
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)

# Cross-Origin Resource Sharing (CORS) with environment-driven whitelisting
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------
# Defensive Error Handlers: Mask Stack Traces & Secrets from Clients
# --------------------------------------------------------------------------

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Formats client and application exceptions in a standardized JSON envelope."""
    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
        headers=headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats Pydantic schema validation failures without leaking internal engine state."""
    formatted_errors = []
    for err in exc.errors():
        field_path = " -> ".join(str(loc) for loc in err.get("loc", []))
        formatted_errors.append({
            "field": field_path,
            "message": err.get("msg", "Invalid field format"),
            "type": err.get("type", "value_error"),
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": True,
            "status_code": 422,
            "detail": "Request payload validation failed.",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(OperationalError)
async def db_operational_exception_handler(request: Request, exc: OperationalError):
    """Gracefully handles database disconnections or unreachability without crashing ASGI pipeline."""
    logger.error(
        "Database connectivity failure on path %s: %s",
        request.url.path,
        str(exc).split("\n")[0],
    )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": True,
            "status_code": 503,
            "detail": "Database service is currently unreachable. Ensure PostgreSQL is active on port 5432, or configure an active DATABASE_URL in backend/.env.",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Prevents exposure of stack traces, database schema details, or environment secrets to clients."""
    incident_ref = f"ERR-{uuid.uuid4().hex[:8].upper()}"
    logger.exception(
        f"Unhandled platform exception [Ref: {incident_ref}] on path {request.url.path}: {str(exc)}"
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": True,
            "status_code": 500,
            "detail": f"Internal server error. Incident reference: {incident_ref}.",
        },
    )


# API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"])
def root_info() -> dict:
    """Root metadata endpoint verifying API service availability."""
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "documentation": "/docs" if settings.ENVIRONMENT != "production" else "disabled_in_prod",
        "health_endpoint": f"{settings.API_V1_PREFIX}/health",
    }
