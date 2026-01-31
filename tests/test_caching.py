"""
Tests for response caching functionality.

Agent 1: Response Caching Implementation
Tests cache behavior, TTL, ETag support, and cache invalidation.
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi import Request, Response

from api.services.cache import (
    CacheEntry,
    ResponseCache,
    add_cache_headers,
    cache_response,
    check_etag_match,
    clear_all_caches,
    get_all_cache_stats,
)


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_cache_entry_creation(self):
        """CacheEntry should store data and metadata."""
        entry = CacheEntry(
            data={"key": "value"}, etag='"abc123"', created_at=time.time(), ttl=3600
        )

        assert entry.data == {"key": "value"}
        assert entry.etag == '"abc123"'
        assert entry.ttl == 3600

    def test_cache_entry_age(self):
        """CacheEntry.age should return seconds since creation."""
        created_at = time.time() - 100  # 100 seconds ago
        entry = CacheEntry(data={}, etag='"test"', created_at=created_at, ttl=3600)

        assert 99 <= entry.age <= 101

    def test_cache_entry_max_age(self):
        """CacheEntry.max_age should return remaining TTL."""
        created_at = time.time() - 100  # 100 seconds ago
        entry = CacheEntry(data={}, etag='"test"', created_at=created_at, ttl=3600)

        # max_age should be approximately ttl - age
        assert 3499 <= entry.max_age <= 3501

    def test_cache_entry_expired_max_age(self):
        """CacheEntry.max_age should return 0 when expired."""
        created_at = time.time() - 4000  # Expired
        entry = CacheEntry(data={}, etag='"test"', created_at=created_at, ttl=3600)

        assert entry.max_age == 0


class TestResponseCache:
    """Tests for ResponseCache class."""

    def setup_method(self):
        """Clear cache instances before each test."""
        clear_all_caches()
        ResponseCache._instances.clear()

    def test_get_instance_creates_singleton(self):
        """get_instance should return same instance for same name."""
        cache1 = ResponseCache.get_instance("test", ttl=3600)
        cache2 = ResponseCache.get_instance("test", ttl=3600)

        assert cache1 is cache2

    def test_get_instance_different_names(self):
        """get_instance should return different instances for different names."""
        cache1 = ResponseCache.get_instance("test1", ttl=3600)
        cache2 = ResponseCache.get_instance("test2", ttl=3600)

        assert cache1 is not cache2

    def test_cache_set_and_get(self):
        """Cache should store and retrieve entries."""
        cache = ResponseCache.get_instance("test_set_get", ttl=3600)

        cache.set("/api/test", {"param": "value"}, {"result": "data"})
        entry = cache.get("/api/test", {"param": "value"})

        assert entry is not None
        assert entry.data == {"result": "data"}

    def test_cache_miss_returns_none(self):
        """Cache should return None for missing entries."""
        cache = ResponseCache.get_instance("test_miss", ttl=3600)

        entry = cache.get("/api/nonexistent", {})

        assert entry is None

    def test_cache_key_includes_params(self):
        """Different params should create different cache entries."""
        cache = ResponseCache.get_instance("test_params", ttl=3600)

        cache.set("/api/test", {"chapter": "I"}, {"chapter": "I"})
        cache.set("/api/test", {"chapter": "II"}, {"chapter": "II"})

        entry1 = cache.get("/api/test", {"chapter": "I"})
        entry2 = cache.get("/api/test", {"chapter": "II"})

        assert entry1.data["chapter"] == "I"
        assert entry2.data["chapter"] == "II"

    def test_cache_invalidate_specific(self):
        """invalidate should remove specific entry."""
        cache = ResponseCache.get_instance("test_invalidate", ttl=3600)

        cache.set("/api/test", {"id": "1"}, {"data": "one"})
        cache.set("/api/test", {"id": "2"}, {"data": "two"})

        cache.invalidate("/api/test", {"id": "1"})

        assert cache.get("/api/test", {"id": "1"}) is None
        assert cache.get("/api/test", {"id": "2"}) is not None

    def test_cache_invalidate_all(self):
        """invalidate without args should clear entire cache."""
        cache = ResponseCache.get_instance("test_invalidate_all", ttl=3600)

        cache.set("/api/test1", {}, {"data": "one"})
        cache.set("/api/test2", {}, {"data": "two"})

        cache.invalidate()

        assert cache.get("/api/test1", {}) is None
        assert cache.get("/api/test2", {}) is None

    def test_cache_stats(self):
        """stats should return cache statistics."""
        cache = ResponseCache.get_instance("test_stats", ttl=3600, maxsize=100)

        cache.set("/api/test1", {}, {"data": "one"})
        cache.set("/api/test2", {}, {"data": "two"})

        stats = cache.stats()

        assert stats["name"] == "test_stats"
        assert stats["size"] == 2
        assert stats["maxsize"] == 100
        assert stats["ttl"] == 3600

    def test_etag_generation(self):
        """Cache should generate valid ETags."""
        cache = ResponseCache.get_instance("test_etag", ttl=3600)

        entry = cache.set("/api/test", {}, {"data": "test"})

        assert entry.etag.startswith('"')
        assert entry.etag.endswith('"')
        assert len(entry.etag) > 2

    def test_etag_consistency(self):
        """Same data should generate same ETag."""
        cache = ResponseCache.get_instance("test_etag_consistent", ttl=3600)

        entry1 = cache.set("/api/test1", {}, {"data": "same"})
        cache.invalidate()
        entry2 = cache.set("/api/test2", {}, {"data": "same"})

        assert entry1.etag == entry2.etag

    def test_cache_disabled(self):
        """Cache should not return entries when disabled in settings."""
        cache = ResponseCache.get_instance("test_disabled", ttl=3600)

        cache.set("/api/test", {}, {"data": "test"})

        with patch("api.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.cache_enabled = False
            entry = cache.get("/api/test", {})

        assert entry is None


class TestAddCacheHeaders:
    """Tests for add_cache_headers function."""

    def test_adds_cache_control_header(self):
        """Should add Cache-Control header."""
        response = Response()
        entry = CacheEntry(data={}, etag='"abc"', created_at=time.time(), ttl=3600)

        add_cache_headers(response, entry)

        assert "Cache-Control" in response.headers
        assert "max-age=" in response.headers["Cache-Control"]
        assert "public" in response.headers["Cache-Control"]

    def test_adds_etag_header(self):
        """Should add ETag header."""
        response = Response()
        entry = CacheEntry(data={}, etag='"abc123"', created_at=time.time(), ttl=3600)

        add_cache_headers(response, entry)

        assert response.headers["ETag"] == '"abc123"'

    def test_adds_cache_hit_header(self):
        """Should add X-Cache: HIT header."""
        response = Response()
        entry = CacheEntry(data={}, etag='"abc"', created_at=time.time(), ttl=3600)

        add_cache_headers(response, entry)

        assert response.headers["X-Cache"] == "HIT"

    def test_adds_age_header(self):
        """Should add Age header."""
        response = Response()
        entry = CacheEntry(
            data={}, etag='"abc"', created_at=time.time() - 100, ttl=3600
        )

        add_cache_headers(response, entry)

        assert "Age" in response.headers
        age = int(response.headers["Age"])
        assert 99 <= age <= 101


class TestCheckEtagMatch:
    """Tests for check_etag_match function."""

    def test_no_if_none_match_header(self):
        """Should return False when no If-None-Match header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = None

        entry = CacheEntry(data={}, etag='"abc"', created_at=time.time(), ttl=3600)

        result = check_etag_match(mock_request, entry)

        assert result is False

    def test_matching_etag(self):
        """Should return True when ETag matches."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = '"abc123"'

        entry = CacheEntry(data={}, etag='"abc123"', created_at=time.time(), ttl=3600)

        result = check_etag_match(mock_request, entry)

        assert result is True

    def test_non_matching_etag(self):
        """Should return False when ETag doesn't match."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = '"xyz789"'

        entry = CacheEntry(data={}, etag='"abc123"', created_at=time.time(), ttl=3600)

        result = check_etag_match(mock_request, entry)

        assert result is False

    def test_multiple_etags_in_header(self):
        """Should match when ETag is one of multiple in header."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = '"aaa", "bbb", "abc123", "ccc"'

        entry = CacheEntry(data={}, etag='"abc123"', created_at=time.time(), ttl=3600)

        result = check_etag_match(mock_request, entry)

        assert result is True

    def test_weak_etag_matching(self):
        """Should handle weak ETags (W/ prefix)."""
        mock_request = MagicMock(spec=Request)
        mock_request.headers.get.return_value = 'W/"abc123"'

        entry = CacheEntry(data={}, etag='"abc123"', created_at=time.time(), ttl=3600)

        result = check_etag_match(mock_request, entry)

        assert result is True


class TestCacheResponseDecorator:
    """Tests for cache_response decorator."""

    def setup_method(self):
        """Clear cache instances before each test."""
        clear_all_caches()
        ResponseCache._instances.clear()

    @pytest.mark.asyncio
    async def test_decorator_caches_response(self):
        """Decorator should cache function result."""
        call_count = 0

        @cache_response("test_decorator")
        async def test_function(request=None):
            nonlocal call_count
            call_count += 1
            return {"data": "result"}

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}
        mock_request.headers.get.return_value = None

        with patch("api.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.cache_enabled = True
            mock_settings.return_value.cache_diseases_ttl = 3600
            mock_settings.return_value.cache_max_size = 1000

            result1 = await test_function(request=mock_request)
            result2 = await test_function(request=mock_request)

        assert result1 == {"data": "result"}
        assert result2 == {"data": "result"}
        assert call_count == 1  # Function called only once

    @pytest.mark.asyncio
    async def test_decorator_bypasses_when_disabled(self):
        """Decorator should bypass cache when disabled."""
        call_count = 0

        @cache_response("test_disabled")
        async def test_function(request=None):
            nonlocal call_count
            call_count += 1
            return {"data": f"call_{call_count}"}

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/test"
        mock_request.query_params = {}

        with patch("api.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.cache_enabled = False

            result1 = await test_function(request=mock_request)
            result2 = await test_function(request=mock_request)

        assert call_count == 2  # Function called twice


class TestCacheUtilityFunctions:
    """Tests for cache utility functions."""

    def setup_method(self):
        """Clear cache instances before each test."""
        clear_all_caches()
        ResponseCache._instances.clear()

    def test_clear_all_caches(self):
        """clear_all_caches should clear all cache instances."""
        cache1 = ResponseCache.get_instance("cache1", ttl=3600)
        cache2 = ResponseCache.get_instance("cache2", ttl=3600)

        cache1.set("/api/test1", {}, {"data": "one"})
        cache2.set("/api/test2", {}, {"data": "two"})

        clear_all_caches()

        assert cache1.get("/api/test1", {}) is None
        assert cache2.get("/api/test2", {}) is None

    def test_get_all_cache_stats(self):
        """get_all_cache_stats should return stats for all caches."""
        cache1 = ResponseCache.get_instance("cache_a", ttl=3600)
        cache2 = ResponseCache.get_instance("cache_b", ttl=7200)

        cache1.set("/api/test1", {}, {"data": "one"})
        cache2.set("/api/test2", {}, {"data": "two"})

        stats = get_all_cache_stats()

        assert len(stats) == 2
        names = [s["name"] for s in stats]
        assert "cache_a" in names
        assert "cache_b" in names


class TestCacheTTLConfiguration:
    """Tests for cache TTL configuration mapping."""

    def setup_method(self):
        """Clear cache instances before each test."""
        clear_all_caches()
        ResponseCache._instances.clear()

    @pytest.mark.asyncio
    async def test_diseases_list_uses_configured_ttl(self):
        """diseases_list cache should use cache_diseases_ttl setting."""

        @cache_response("diseases_list")
        async def test_function(request=None):
            return {"diseases": []}

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/diseases"
        mock_request.query_params = {}
        mock_request.headers.get.return_value = None

        with patch("api.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.cache_enabled = True
            mock_settings.return_value.cache_diseases_ttl = 86400  # 24h
            mock_settings.return_value.cache_max_size = 1000

            await test_function(request=mock_request)

        cache = ResponseCache._instances.get("diseases_list")
        assert cache is not None
        assert cache.ttl == 86400

    @pytest.mark.asyncio
    async def test_disease_detail_uses_configured_ttl(self):
        """disease_detail cache should use cache_disease_detail_ttl setting."""

        @cache_response("disease_detail")
        async def test_function(request=None):
            return {"id": 1, "name": "Test"}

        mock_request = MagicMock(spec=Request)
        mock_request.url.path = "/api/diseases/1"
        mock_request.query_params = {}
        mock_request.headers.get.return_value = None

        with patch("api.services.cache.get_settings") as mock_settings:
            mock_settings.return_value.cache_enabled = True
            mock_settings.return_value.cache_diseases_ttl = 86400
            mock_settings.return_value.cache_disease_detail_ttl = 3600  # 1h
            mock_settings.return_value.cache_max_size = 1000

            await test_function(request=mock_request)

        cache = ResponseCache._instances.get("disease_detail")
        assert cache is not None
        assert cache.ttl == 3600
