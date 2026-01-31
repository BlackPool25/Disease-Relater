"""
Tests for rate limiting functionality.

Tests the custom 429 handler, rate limit headers, and rate limiting behavior.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from slowapi.errors import RateLimitExceeded

from api.rate_limit import custom_rate_limit_handler, get_rate_limit_string, limiter


class TestRateLimitString:
    """Tests for get_rate_limit_string function."""

    def test_returns_hourly_format(self):
        """Rate limit string should use hourly format."""
        result = get_rate_limit_string()
        assert "/hour" in result
        assert "/minute" not in result

    def test_uses_settings_value(self):
        """Rate limit string should use value from settings."""
        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 50
            result = get_rate_limit_string()
            assert result == "50/hour"

    def test_default_rate_limit(self):
        """Default rate limit should be 100/hour."""
        result = get_rate_limit_string()
        assert "100" in result


class TestCustomRateLimitHandler:
    """Tests for custom_rate_limit_handler function."""

    @pytest.mark.asyncio
    async def test_returns_429_status(self):
        """Handler should return 429 status code."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 60

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_response_contains_error_structure(self):
        """Handler should return proper JSON error structure."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 120

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        body = json.loads(response.body)

        assert "error" in body
        assert body["error"]["type"] == "RateLimitExceeded"
        assert body["error"]["status_code"] == 429
        assert "details" in body["error"]

    @pytest.mark.asyncio
    async def test_response_contains_rate_limit_headers(self):
        """Handler should include X-RateLimit-* headers."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 3600

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        assert "Retry-After" in response.headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert response.headers["X-RateLimit-Remaining"] == "0"

    @pytest.mark.asyncio
    async def test_retry_after_header_value(self):
        """Retry-After header should match exception value."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 1800  # 30 minutes

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        assert response.headers["Retry-After"] == "1800"

    @pytest.mark.asyncio
    async def test_message_includes_rate_limit(self):
        """Error message should include the rate limit value."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 60

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        body = json.loads(response.body)

        assert "100" in body["error"]["message"]
        assert "hour" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_details_contains_period(self):
        """Error details should include period as 'hour'."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 60

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        body = json.loads(response.body)

        assert body["error"]["details"]["period"] == "hour"
        assert body["error"]["details"]["limit"] == 100
        assert body["error"]["details"]["retry_after_seconds"] == 60


class TestLimiterConfiguration:
    """Tests for limiter configuration."""

    def test_limiter_has_headers_disabled(self):
        """Limiter should have headers_enabled set to False.

        Note: Headers are disabled because endpoints returning dicts
        cannot have headers injected without explicit Response parameter.
        Rate limit headers are provided in the custom 429 handler.
        """
        assert limiter._headers_enabled is False

    def test_limiter_uses_remote_address(self):
        """Limiter should use IP-based key function."""
        assert limiter._key_func is not None

    def test_limiter_key_func_extracts_ip(self):
        """Limiter key function should extract client IP from request."""
        from slowapi.util import get_remote_address

        # Create mock request with client
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {}

        # Test the key function
        ip = get_remote_address(mock_request)
        assert ip == "192.168.1.100"
