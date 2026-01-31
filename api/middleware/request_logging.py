"""
Request Logging Middleware for Disease-Relater API.

Provides request/response logging with timing information for
monitoring and debugging API performance.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from api.config import get_settings

# Use a dedicated logger for request logging to enable filtering
logger = logging.getLogger("api.request_logging")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests with response time tracking.

    Logs each request with:
    - HTTP method and path
    - Client IP address
    - Response status code
    - Response time in milliseconds

    Also adds X-Response-Time header to all responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log timing information.

        Args:
            request: The incoming HTTP request
            call_next: Function to call the next middleware/endpoint

        Returns:
            Response with X-Response-Time header added
        """
        start_time = time.perf_counter()

        # Get client IP (handle proxy headers securely)
        client_ip = self._get_client_ip(request)

        # Log incoming request
        logger.info(f"Request: {request.method} {request.url.path} - IP: {client_ip}")

        # Process the request
        response = await call_next(request)

        # Calculate response time
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response with timing
        logger.info(
            f"Response: {request.method} {request.url.path} - "
            f"{response.status_code} - {duration_ms:.2f}ms"
        )

        # Add timing header for client visibility
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request securely.

        Only trusts X-Forwarded-For header when trust_proxy setting is enabled.
        This prevents IP spoofing attacks when the application is directly
        exposed to the internet.

        Args:
            request: The incoming HTTP request

        Returns:
            Client IP address string
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
