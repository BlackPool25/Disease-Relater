"""
Response Caching Service

Agent 1: Response Caching Implementation
Provides in-memory TTL-based caching for GET endpoints with ETag support.
"""

import hashlib
import json
import threading
import time
from functools import wraps
from typing import Any, Callable, Optional

from cachetools import TTLCache
from fastapi import Request, Response
from pydantic import BaseModel

from api.config import get_settings


class CacheEntry:
    """Represents a cached response with metadata."""

    def __init__(self, data: Any, etag: str, created_at: float, ttl: int):
        self.data = data
        self.etag = etag
        self.created_at = created_at
        self.ttl = ttl

    @property
    def age(self) -> int:
        """Get the age of the cache entry in seconds."""
        return int(time.time() - self.created_at)

    @property
    def max_age(self) -> int:
        """Get remaining max-age for Cache-Control header."""
        remaining = self.ttl - self.age
        return max(0, remaining)


class ResponseCache:
    """Thread-safe response cache with TTL support.

    Provides caching for FastAPI route responses with:
    - TTL-based expiration
    - ETag generation and validation
    - Cache-Control header support
    - Thread-safe operations
    """

    _instances: dict[str, "ResponseCache"] = {}
    _lock = threading.Lock()

    def __init__(self, name: str, ttl: int, maxsize: int = 1000):
        """Initialize a named cache instance.

        Args:
            name: Unique name for this cache (e.g., 'diseases', 'network')
            ttl: Time-to-live in seconds
            maxsize: Maximum number of entries
        """
        self.name = name
        self.ttl = ttl
        self.maxsize = maxsize
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = threading.Lock()

    @classmethod
    def get_instance(cls, name: str, ttl: int, maxsize: int = 1000) -> "ResponseCache":
        """Get or create a named cache instance (singleton per name).

        Args:
            name: Unique name for this cache
            ttl: Time-to-live in seconds
            maxsize: Maximum number of entries

        Returns:
            ResponseCache instance
        """
        with cls._lock:
            if name not in cls._instances:
                cls._instances[name] = cls(name, ttl, maxsize)
            return cls._instances[name]

    def _generate_cache_key(self, path: str, params: dict) -> str:
        """Generate a unique cache key from path and query parameters.

        Args:
            path: Request path
            params: Query parameters dict

        Returns:
            Unique cache key string
        """
        # Sort params for consistent key generation
        sorted_params = sorted(params.items()) if params else []
        key_data = f"{path}:{json.dumps(sorted_params, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _generate_etag(self, data: Any) -> str:
        """Generate an ETag from response data.

        Args:
            data: Response data (will be JSON serialized)

        Returns:
            ETag string with quotes
        """
        if isinstance(data, BaseModel):
            content = data.model_dump_json()
        elif isinstance(data, (dict, list)):
            content = json.dumps(data, sort_keys=True, default=str)
        else:
            content = str(data)

        hash_value = hashlib.md5(content.encode()).hexdigest()[:16]
        return f'"{hash_value}"'

    def get(self, path: str, params: dict) -> Optional[CacheEntry]:
        """Get a cached entry if it exists.

        Args:
            path: Request path
            params: Query parameters dict

        Returns:
            CacheEntry if found and valid, None otherwise
        """
        settings = get_settings()
        if not settings.cache_enabled:
            return None

        key = self._generate_cache_key(path, params)
        with self._lock:
            return self._cache.get(key)

    def set(self, path: str, params: dict, data: Any) -> CacheEntry:
        """Cache a response.

        Args:
            path: Request path
            params: Query parameters dict
            data: Response data to cache

        Returns:
            CacheEntry containing the cached data
        """
        key = self._generate_cache_key(path, params)
        etag = self._generate_etag(data)
        entry = CacheEntry(data=data, etag=etag, created_at=time.time(), ttl=self.ttl)

        with self._lock:
            self._cache[key] = entry

        return entry

    def invalidate(self, path: Optional[str] = None, params: Optional[dict] = None):
        """Invalidate cache entries.

        Args:
            path: If provided with params, invalidate specific entry.
                  If None, clear entire cache.
            params: Query parameters for specific entry invalidation
        """
        with self._lock:
            if path is not None and params is not None:
                key = self._generate_cache_key(path, params)
                self._cache.pop(key, None)
            else:
                self._cache.clear()

    def stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dict with cache statistics
        """
        with self._lock:
            return {
                "name": self.name,
                "size": len(self._cache),
                "maxsize": self.maxsize,
                "ttl": self.ttl,
            }


def add_cache_headers(response: Response, entry: CacheEntry) -> Response:
    """Add caching headers to a response.

    Args:
        response: FastAPI Response object
        entry: CacheEntry with cache metadata

    Returns:
        Response with caching headers added
    """
    response.headers["Cache-Control"] = f"public, max-age={entry.max_age}"
    response.headers["ETag"] = entry.etag
    response.headers["X-Cache"] = "HIT"
    response.headers["Age"] = str(entry.age)
    return response


def check_etag_match(request: Request, entry: CacheEntry) -> bool:
    """Check if request ETag matches cached ETag.

    Args:
        request: FastAPI Request object
        entry: CacheEntry to check against

    Returns:
        True if ETag matches (304 can be returned)
    """
    if_none_match = request.headers.get("If-None-Match")
    if not if_none_match:
        return False

    # Handle multiple ETags in If-None-Match header
    etags = [tag.strip().strip("W/") for tag in if_none_match.split(",")]
    return entry.etag.strip('"') in [tag.strip('"') for tag in etags]


def cache_response(
    cache_name: str, ttl_seconds: Optional[int] = None, maxsize: int = 1000
) -> Callable:
    """Decorator for caching FastAPI route responses.

    This decorator wraps async route handlers to add response caching
    with TTL expiration and ETag support.

    Args:
        cache_name: Unique name for this cache
        ttl_seconds: TTL in seconds (uses config default if None)
        maxsize: Maximum cache entries

    Returns:
        Decorator function

    Example:
        @router.get("/items")
        @cache_response("items", ttl_seconds=3600)
        async def get_items(request: Request):
            return {"items": [...]}
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Find request in kwargs (injected by FastAPI)
            request: Optional[Request] = kwargs.get("request")

            # Get settings for TTL
            settings = get_settings()
            if not settings.cache_enabled:
                return await func(*args, **kwargs)

            # Determine actual TTL based on cache name or explicit value
            if ttl_seconds is not None:
                actual_ttl = ttl_seconds
            else:
                # Map cache names to their configured TTLs
                ttl_map = {
                    "diseases_list": settings.cache_diseases_ttl,
                    "disease_detail": settings.cache_disease_detail_ttl,
                    "network": settings.cache_network_ttl,
                    "chapters": settings.cache_chapters_ttl,
                }
                actual_ttl = ttl_map.get(cache_name, settings.cache_diseases_ttl)

            # Get or create cache instance
            cache = ResponseCache.get_instance(
                cache_name,
                ttl=actual_ttl,
                maxsize=min(maxsize, settings.cache_max_size),
            )

            # Build cache key from request path and query params
            if request:
                path = request.url.path
                params = dict(request.query_params)
            else:
                path = cache_name
                params = {}

            # Check cache
            entry = cache.get(path, params)

            if entry is not None:
                # Check for ETag match (304 Not Modified)
                if request and check_etag_match(request, entry):
                    response = Response(
                        status_code=304,
                        headers={
                            "ETag": entry.etag,
                            "Cache-Control": f"public, max-age={entry.max_age}",
                            "X-Cache": "HIT-NOT-MODIFIED",
                        },
                    )
                    return response

                # Return cached data
                # Note: Headers will be added by the route or middleware
                return entry.data

            # Cache miss - call the actual function
            result = await func(*args, **kwargs)

            # Cache the result
            cache.set(path, params, result)

            return result

        return wrapper

    return decorator


# Pre-configured cache instances based on route patterns
def get_diseases_cache() -> ResponseCache:
    """Get cache for /diseases list endpoint."""
    settings = get_settings()
    return ResponseCache.get_instance(
        "diseases_list",
        ttl=settings.cache_diseases_ttl,
        maxsize=settings.cache_max_size,
    )


def get_disease_detail_cache() -> ResponseCache:
    """Get cache for /diseases/:id endpoint."""
    settings = get_settings()
    return ResponseCache.get_instance(
        "disease_detail",
        ttl=settings.cache_disease_detail_ttl,
        maxsize=settings.cache_max_size,
    )


def get_network_cache() -> ResponseCache:
    """Get cache for /network endpoint."""
    settings = get_settings()
    return ResponseCache.get_instance(
        "network", ttl=settings.cache_network_ttl, maxsize=settings.cache_max_size
    )


def get_chapters_cache() -> ResponseCache:
    """Get cache for /chapters endpoint."""
    settings = get_settings()
    return ResponseCache.get_instance(
        "chapters", ttl=settings.cache_chapters_ttl, maxsize=settings.cache_max_size
    )


def clear_all_caches():
    """Clear all response caches. Useful for testing or data updates."""
    with ResponseCache._lock:
        for cache in ResponseCache._instances.values():
            cache.invalidate()


def get_all_cache_stats() -> list[dict]:
    """Get statistics for all cache instances.

    Returns:
        List of cache statistics dicts
    """
    with ResponseCache._lock:
        return [cache.stats() for cache in ResponseCache._instances.values()]
