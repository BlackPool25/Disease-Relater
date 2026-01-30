"""
Rate Limiting Configuration for Disease-Relater API.

Provides a shared rate limiter instance that can be imported by routes
without circular import issues.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from api.config import get_settings

# Initialize rate limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_string() -> str:
    """Get the rate limit string based on settings.

    Returns:
        Rate limit string in format "N/minute" (e.g., "100/minute")
    """
    settings = get_settings()
    return f"{settings.api_rate_limit}/minute"
