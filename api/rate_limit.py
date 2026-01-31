"""
Rate Limiting Configuration for Disease-Relater API.

Provides a shared rate limiter instance with custom 429 error handling
and rate limit headers for client feedback.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded

from api.config import get_settings


def get_client_ip_for_rate_limit(request: Request) -> str:
    """Securely extract client IP for rate limiting.

    Only trusts X-Forwarded-For header when trust_proxy setting is enabled.
    This prevents IP spoofing attacks that could bypass rate limiting.

    Args:
        request: The incoming HTTP request

    Returns:
        Client IP address string for rate limiting key
    """
    settings = get_settings()

    # Only trust X-Forwarded-For if explicitly configured to trust proxy
    if settings.trust_proxy:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

    # Fall back to direct client host
    if request.client:
        return request.client.host

    return "unknown"


# Initialize rate limiter with secure IP-based key function
# Note: headers_enabled is set to False because endpoints returning dicts
# cannot have headers injected without explicit Response parameter.
# Rate limit headers are provided in the custom 429 handler when limit is exceeded.
limiter = Limiter(
    key_func=get_client_ip_for_rate_limit,
    headers_enabled=False,
)


def get_rate_limit_string() -> str:
    """Get the rate limit string based on settings.

    Returns:
        Rate limit string in format "N/minute" (e.g., "100/minute")
    """
    settings = get_settings()
    return f"{settings.api_rate_limit}/minute"


async def custom_rate_limit_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Custom 429 handler matching API error format.

    Returns a JSON response with rate limit details and appropriate headers
    to help clients understand when they can retry.

    Args:
        request: The incoming request that exceeded the rate limit
        exc: The RateLimitExceeded exception with limit details

    Returns:
        JSONResponse with 429 status and rate limit headers
    """
    settings = get_settings()

    # Extract retry_after value (seconds until reset)
    retry_after = getattr(exc, "retry_after", 60)

    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "type": "RateLimitExceeded",
                "message": f"Rate limit exceeded: {settings.api_rate_limit} requests per minute",
                "details": {
                    "retry_after_seconds": retry_after,
                    "limit": settings.api_rate_limit,
                    "period": "minute",
                },
                "status_code": 429,
            }
        },
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(settings.api_rate_limit),
            "X-RateLimit-Remaining": "0",
        },
    )
