"""
Tests for rate limiting functionality.

Tests the custom 429 handler, rate limit headers, and rate limiting behavior.
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi import Request
from slowapi.errors import RateLimitExceeded

from api.rate_limit import (
    custom_rate_limit_handler,
    get_rate_limit_string,
    get_client_ip_for_rate_limit,
    limiter,
)


class TestRateLimitString:
    """Tests for get_rate_limit_string function."""

    def test_returns_minute_format(self):
        """Rate limit string should use minute format."""
        result = get_rate_limit_string()
        assert "/minute" in result
        assert "/hour" not in result

    def test_uses_settings_value(self):
        """Rate limit string should use value from settings."""
        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 50
            result = get_rate_limit_string()
            assert result == "50/minute"

    def test_default_rate_limit(self):
        """Default rate limit should be 100/minute."""
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
        mock_exc.retry_after = 60

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
        mock_exc.retry_after = 30  # 30 seconds

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        assert response.headers["Retry-After"] == "30"

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
        assert "minute" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_details_contains_period(self):
        """Error details should include period as 'minute'."""
        mock_request = MagicMock(spec=Request)
        mock_exc = MagicMock(spec=RateLimitExceeded)
        mock_exc.retry_after = 60

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.api_rate_limit = 100
            response = await custom_rate_limit_handler(mock_request, mock_exc)

        body = json.loads(response.body)

        assert body["error"]["details"]["period"] == "minute"
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

    def test_limiter_uses_secure_key_function(self):
        """Limiter should use the secure IP-based key function."""
        assert limiter._key_func is not None
        assert limiter._key_func == get_client_ip_for_rate_limit


class TestGetClientIpForRateLimit:
    """Tests for get_client_ip_for_rate_limit function."""

    def test_returns_direct_client_ip_when_trust_proxy_false(self):
        """Should return direct client IP when trust_proxy is False."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1"}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = get_client_ip_for_rate_limit(mock_request)

        # Should ignore X-Forwarded-For and use direct client
        assert result == "192.168.1.100"

    def test_uses_x_forwarded_for_when_trust_proxy_true(self):
        """Should use X-Forwarded-For when trust_proxy is True."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = get_client_ip_for_rate_limit(mock_request)

        # Should use first IP from X-Forwarded-For
        assert result == "203.0.113.50"

    def test_handles_single_x_forwarded_for_ip(self):
        """Should handle single IP in X-Forwarded-For header."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.100"}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = get_client_ip_for_rate_limit(mock_request)

        assert result == "203.0.113.100"

    def test_strips_whitespace_from_forwarded_ip(self):
        """Should strip whitespace from X-Forwarded-For IP."""
        mock_request = MagicMock()
        mock_request.headers = {"X-Forwarded-For": "  203.0.113.100  , 10.0.0.1"}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = get_client_ip_for_rate_limit(mock_request)

        assert result == "203.0.113.100"

    def test_returns_direct_ip_when_no_forwarded_header(self):
        """Should use client IP when no X-Forwarded-For header present."""
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = get_client_ip_for_rate_limit(mock_request)

        assert result == "192.168.1.100"

    def test_returns_unknown_when_no_client(self):
        """Should return 'unknown' when client info is not available."""
        mock_request = MagicMock()
        mock_request.client = None
        mock_request.headers = {}

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = get_client_ip_for_rate_limit(mock_request)

        assert result == "unknown"

    def test_spoofing_prevented_when_trust_proxy_false(self):
        """Should prevent IP spoofing by ignoring X-Forwarded-For when trust_proxy is False.

        This is a security-critical test. When trust_proxy is False, malicious clients
        cannot bypass rate limiting by setting a fake X-Forwarded-For header.
        """
        mock_request = MagicMock()
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"  # Real IP
        mock_request.headers = {"X-Forwarded-For": "fake.ip.address"}  # Spoofed

        with patch("api.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = get_client_ip_for_rate_limit(mock_request)

        # Must use real client IP, not spoofed header
        assert result == "192.168.1.100"
        assert result != "fake.ip.address"
