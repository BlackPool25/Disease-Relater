"""
Health check endpoint for Disease-Relater API.

Provides API health status and database connectivity checks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from api.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    database: str
    timestamp: str
    uptime_seconds: Optional[float] = None


class HealthCheckResult(BaseModel):
    """Detailed health check result."""

    status: str
    checks: Dict[str, Any]


# Track server start time for uptime calculation
import time

_server_start_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns API health status and database connectivity information.",
    responses={
        200: {"description": "API is healthy"},
        503: {"description": "API is unhealthy or database disconnected"},
    },
)
async def health_check() -> HealthResponse:
    """Get API health status.

    Returns basic health information including:
    - API status (healthy/unhealthy)
    - Version information
    - Database connectivity status
    - Server uptime

    Returns:
        HealthResponse with status details

    Example:
        >>> curl http://localhost:5000/api/health
        {
            "status": "healthy",
            "version": "1.0.0",
            "database": "connected",
            "timestamp": "2026-01-30T12:00:00Z",
            "uptime_seconds": 3600
        }
    """
    from datetime import datetime, timezone

    settings = get_settings()
    uptime = time.time() - _server_start_time

    # Check database connectivity (placeholder - will be implemented with actual DB checks)
    db_status = "connected"  # TODO: Add actual DB connectivity check

    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database=db_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        uptime_seconds=round(uptime, 2),
    )


@router.get(
    "/health/detailed",
    response_model=HealthCheckResult,
    summary="Detailed health check",
    description="Returns detailed health information including all component checks.",
    include_in_schema=False,  # Hide from public docs (internal use)
)
async def health_check_detailed() -> HealthCheckResult:
    """Get detailed health status for monitoring.

    Returns comprehensive health information for monitoring systems.
    Includes individual component status checks.

    Returns:
        HealthCheckResult with detailed status

    Raises:
        HTTPException: If critical components are unhealthy (503)
    """
    from datetime import datetime, timezone

    settings = get_settings()
    checks = {}

    # Check API configuration
    try:
        checks["config"] = {
            "status": "ok",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "debug_mode": settings.debug,
        }
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        checks["config"] = {"status": "error", "message": "Configuration error"}

    # Check database (placeholder)
    try:
        # TODO: Add actual database connectivity check
        checks["database"] = {"status": "ok", "message": "Database connection active"}
    except Exception as e:
        logger.error(f"Database check failed: {e}")
        checks["database"] = {
            "status": "error",
            "message": "Database connection failed",
        }

    # Determine overall status
    all_ok = all(check.get("status") == "ok" for check in checks.values())
    overall_status = "healthy" if all_ok else "unhealthy"

    if not all_ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": overall_status,
                "checks": checks,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return HealthCheckResult(status=overall_status, checks=checks)


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Kubernetes-style readiness probe endpoint.",
    responses={
        200: {"description": "Service is ready to accept traffic"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check() -> Dict[str, str]:
    """Readiness probe for container orchestration.

    Returns 200 when the service is ready to accept traffic,
    503 when it's not ready (e.g., during startup or shutdown).

    Returns:
        Dict with status
    """
    # TODO: Add actual readiness checks (DB connection, etc.)
    return {"status": "ready"}


@router.get(
    "/live",
    summary="Liveness probe",
    description="Kubernetes-style liveness probe endpoint.",
    responses={
        200: {"description": "Service is alive"},
        503: {"description": "Service is not alive (should be restarted)"},
    },
)
async def liveness_check() -> Dict[str, str]:
    """Liveness probe for container orchestration.

    Returns 200 when the service is alive and should not be restarted,
    503 when it's dead/unhealthy and should be restarted.

    Returns:
        Dict with status
    """
    return {"status": "alive"}
