"""
Health check endpoint for Disease-Relater API.

Provides API health status and database connectivity checks.
Uses actual database queries to verify connectivity rather than hardcoded values.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from supabase import AsyncClient
from typing import Dict, Any, Optional
import logging
import time

from api.config import get_settings
from api.dependencies import get_supabase_client
from api.rate_limit import limiter, get_rate_limit_string

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

# Get rate limit string for decorators
_rate_limit = get_rate_limit_string()


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
_server_start_time = time.time()


async def _check_database_connectivity(supabase: AsyncClient) -> str:
    """Check database connectivity with a simple query.

    Performs a lightweight query to verify the database is accessible.
    Does not expose any sensitive information on failure.

    Args:
        supabase: Supabase async client

    Returns:
        "connected" if database is accessible and has data
        "empty" if database is accessible but has no data
        "disconnected" if database is not accessible
    """
    try:
        # Simple query to check if database is reachable
        # Using limit(1) to minimize data transfer
        result = await supabase.table("diseases").select("icd_code").limit(1).execute()

        if result.data:
            return "connected"
        else:
            return "empty"
    except Exception as e:
        # Log the error for debugging but don't expose details to client
        logger.warning(f"Database connectivity check failed: {e}")
        return "disconnected"


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
@limiter.limit(_rate_limit)
async def health_check(
    request: Request,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> HealthResponse:
    """Get API health status.

    Returns basic health information including:
    - API status (healthy/unhealthy)
    - Version information
    - Database connectivity status (verified via actual query)
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

    # Verify database connectivity with a simple query
    db_status = await _check_database_connectivity(supabase)

    # Return unhealthy status if database is disconnected
    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "version": settings.app_version,
                "database": db_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

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
@limiter.limit(_rate_limit)
async def health_check_detailed(
    request: Request,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> HealthCheckResult:
    """Get detailed health status for monitoring.

    Returns comprehensive health information for monitoring systems.
    Includes individual component status checks with actual database verification.

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

    # Check database connectivity with actual query
    try:
        db_status = await _check_database_connectivity(supabase)
        if db_status == "connected":
            checks["database"] = {
                "status": "ok",
                "message": "Database connection active",
            }
        elif db_status == "empty":
            checks["database"] = {
                "status": "ok",
                "message": "Database connected but empty",
            }
        else:
            checks["database"] = {
                "status": "error",
                "message": "Database connection failed",
            }
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
@limiter.limit(_rate_limit)
async def readiness_check(
    request: Request,
    supabase: AsyncClient = Depends(get_supabase_client),
) -> Dict[str, str]:
    """Readiness probe for container orchestration.

    Returns 200 when the service is ready to accept traffic
    (database is connected and accessible).
    Returns 503 when it's not ready (e.g., database unavailable).

    Returns:
        Dict with status
    """
    # Check database connectivity for readiness
    db_status = await _check_database_connectivity(supabase)

    if db_status == "disconnected":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "reason": "database_unavailable"},
        )

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
@limiter.limit(_rate_limit)
async def liveness_check(request: Request) -> Dict[str, str]:
    """Liveness probe for container orchestration.

    Returns 200 when the service is alive and should not be restarted,
    503 when it's dead/unhealthy and should be restarted.

    Returns:
        Dict with status
    """
    return {"status": "alive"}
