"""
Tests for request logging middleware.

Tests the RequestLoggingMiddleware for proper logging and timing headers.
"""

import logging
import pytest
from unittest.mock import MagicMock, patch
from starlette.requests import Request
from starlette.responses import Response

from api.middleware.request_logging import RequestLoggingMiddleware


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware class."""

    @pytest.mark.asyncio
    async def test_adds_response_time_header(self):
        """Middleware should add X-Response-Time header to responses."""

        async def mock_app(scope, receive, send):
            response = Response(content="OK", status_code=200)
            await response(scope, receive, send)

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            response = await middleware.dispatch(mock_request, mock_call_next)

        assert "X-Response-Time" in response.headers
        assert "ms" in response.headers["X-Response-Time"]

    @pytest.mark.asyncio
    async def test_logs_request_info(self, caplog):
        """Middleware should log request method and path."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/diseases"
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        with caplog.at_level(logging.INFO, logger="api.request_logging"):
            with patch("api.middleware.request_logging.get_settings") as mock_settings:
                mock_settings.return_value.trust_proxy = False
                await middleware.dispatch(mock_request, mock_call_next)

        log_messages = [record.message for record in caplog.records]
        request_logged = any(
            "POST" in msg and "/api/diseases" in msg for msg in log_messages
        )
        assert request_logged

    @pytest.mark.asyncio
    async def test_logs_response_status(self, caplog):
        """Middleware should log response status code."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/health"
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=201)

        async def mock_call_next(request):
            return mock_response

        with caplog.at_level(logging.INFO, logger="api.request_logging"):
            with patch("api.middleware.request_logging.get_settings") as mock_settings:
                mock_settings.return_value.trust_proxy = False
                await middleware.dispatch(mock_request, mock_call_next)

        log_messages = [record.message for record in caplog.records]
        response_logged = any("201" in msg for msg in log_messages)
        assert response_logged

    @pytest.mark.asyncio
    async def test_logs_response_time(self, caplog):
        """Middleware should log response time in ms."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        with caplog.at_level(logging.INFO, logger="api.request_logging"):
            with patch("api.middleware.request_logging.get_settings") as mock_settings:
                mock_settings.return_value.trust_proxy = False
                await middleware.dispatch(mock_request, mock_call_next)

        log_messages = [record.message for record in caplog.records]
        # Response log should contain "ms" for milliseconds
        response_logged = any("ms" in msg for msg in log_messages)
        assert response_logged


class TestGetClientIP:
    """Tests for _get_client_ip method."""

    def test_returns_direct_client_ip_when_trust_proxy_false(self):
        """Should return direct client IP when trust_proxy is False."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {"X-Forwarded-For": "10.0.0.1"}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = middleware._get_client_ip(mock_request)

        # Should ignore X-Forwarded-For and return direct client
        assert result == "192.168.1.100"

    def test_respects_x_forwarded_for_header_when_trust_proxy_true(self):
        """Should use X-Forwarded-For header when trust_proxy is True."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "10.0.0.1"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.50, 70.41.3.18"}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = middleware._get_client_ip(mock_request)

        assert result == "203.0.113.50"

    def test_handles_single_x_forwarded_for(self):
        """Should handle single IP in X-Forwarded-For when trust_proxy is True."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "203.0.113.100"}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = middleware._get_client_ip(mock_request)

        assert result == "203.0.113.100"

    def test_returns_unknown_when_no_client(self):
        """Should return 'unknown' when client info is not available."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = None
        mock_request.headers = {}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = middleware._get_client_ip(mock_request)

        assert result == "unknown"

    def test_strips_whitespace_from_x_forwarded_for(self):
        """Should strip whitespace from X-Forwarded-For IP when trust_proxy is True."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.headers = {"X-Forwarded-For": "  203.0.113.100  , 10.0.0.1"}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = middleware._get_client_ip(mock_request)

        assert result == "203.0.113.100"

    def test_falls_back_to_direct_ip_when_no_forwarded_header(self):
        """Should use direct client IP when no X-Forwarded-For header present."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"
        mock_request.headers = {}

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = True
            result = middleware._get_client_ip(mock_request)

        assert result == "192.168.1.100"

    def test_spoofing_prevented_when_trust_proxy_false(self):
        """Should prevent IP spoofing by ignoring X-Forwarded-For when trust_proxy is False.

        This is a security-critical test. When trust_proxy is False, malicious clients
        cannot spoof their IP by setting a fake X-Forwarded-For header.
        """

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.100"  # Real IP
        mock_request.headers = {"X-Forwarded-For": "spoofed.ip.address"}  # Spoofed

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            result = middleware._get_client_ip(mock_request)

        # Must use real client IP, not spoofed header
        assert result == "192.168.1.100"
        assert result != "spoofed.ip.address"


class TestResponseTimeHeader:
    """Tests for response time header format."""

    @pytest.mark.asyncio
    async def test_response_time_format(self):
        """X-Response-Time should be in format like '0.12ms'."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            response = await middleware.dispatch(mock_request, mock_call_next)

        timing = response.headers["X-Response-Time"]
        # Should end with "ms"
        assert timing.endswith("ms")
        # Should be parseable as float (without ms suffix)
        numeric_part = timing[:-2]
        assert float(numeric_part) >= 0

    @pytest.mark.asyncio
    async def test_response_time_is_positive(self):
        """Response time should be a positive number."""

        async def mock_app(scope, receive, send):
            pass

        middleware = RequestLoggingMiddleware(mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/test"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}

        mock_response = Response(content="OK", status_code=200)

        async def mock_call_next(request):
            return mock_response

        with patch("api.middleware.request_logging.get_settings") as mock_settings:
            mock_settings.return_value.trust_proxy = False
            response = await middleware.dispatch(mock_request, mock_call_next)

        timing = response.headers["X-Response-Time"]
        numeric_value = float(timing.replace("ms", ""))
        assert numeric_value >= 0
