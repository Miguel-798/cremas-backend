"""
Cache - Infrastructure Layer

In-memory cache abstraction using cachetools TTLCache.
Provides a protocol-based design for easy swap to Redis later.
"""
from typing import Any, Optional

from cachetools import TTLCache

from src.infrastructure.config import settings
from src.infrastructure.logging import get_logger

log = get_logger(__name__)


# ============================================
# Cache Protocol
# ============================================

class CacheProtocol:
    """Protocol defining the cache interface (can be sync or async)."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if not found or expired."""
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache with optional TTL override."""
        raise NotImplementedError
    
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        raise NotImplementedError
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        raise NotImplementedError
    
    def stats(self) -> dict:
        """Return cache statistics."""
        raise NotImplementedError


# ============================================
# Cache Keys — centralized key factory
# ============================================

class CacheKeys:
    """Factory for consistent cache key generation."""
    
    PREFIX = "gentleman"
    
    @classmethod
    def creams(cls) -> str:
        """Key for all creams list."""
        return f"{cls.PREFIX}:creams:all"
    
    @classmethod
    def cream_by_id(cls, cream_id: str) -> str:
        """Key for a single cream by ID."""
        return f"{cls.PREFIX}:creams:{cream_id}"
    
    @classmethod
    def low_stock(cls) -> str:
        """Key for low stock list."""
        return f"{cls.PREFIX}:creams:low_stock"
    
    @classmethod
    def active_reservations(cls) -> str:
        """Key for active reservations list."""
        return f"{cls.PREFIX}:reservations:active"
    
    @classmethod
    def sales(cls) -> str:
        """Key for all sales list."""
        return f"{cls.PREFIX}:sales:all"
    
    @classmethod
    def sales_by_cream(cls, cream_id: str) -> str:
        """Key for sales of a specific cream."""
        return f"{cls.PREFIX}:sales:{cream_id}"


# ============================================
# Memory Cache TTLs
# ============================================

CACHE_TTL = {
    "creams": 60,          # 60 seconds
    "cream_by_id": 120,    # 120 seconds
    "low_stock": 30,       # 30 seconds
    "reservations": 30,     # 30 seconds
    "sales": 30,           # 30 seconds
    "default": 60,         # fallback TTL
}


# ============================================
# MemoryCache Implementation
# ============================================

class MemoryCache(CacheProtocol):
    """
    In-memory TTL cache using cachetools.TTLCache.
    
    Thread-safe, non-blocking. TTL is enforced by cachetools.
    Cache stats (hits/misses) are tracked manually.
    """
    
    def __init__(self, maxsize: int = 128, ttl: Optional[int] = None):
        self._ttl = ttl or CACHE_TTL["default"]
        self._cache = TTLCache(maxsize=maxsize, ttl=self._ttl)
        self._hits = 0
        self._misses = 0
        self._sets = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache, tracking hits/misses."""
        if key in self._cache:
            self._hits += 1
            log.debug("cache.hit", key=key)
            return self._cache[key]
        self._misses += 1
        log.debug("cache.miss", key=key)
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache. If ttl is specified, a fresh TTLCache entry is used."""
        if ttl is not None and ttl != self._ttl:
            # Create a new mini-cache entry for this specific TTL
            entry_cache = TTLCache(maxsize=1, ttl=ttl)
            entry_cache[key] = value
            self._cache[key] = entry_cache
        else:
            self._cache[key] = value
        self._sets += 1
        log.debug("cache.set", key=key, ttl=ttl or self._ttl)
    
    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            log.debug("cache.delete", key=key)
    
    async def clear(self) -> None:
        """Clear all cache entries and reset stats."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._sets = 0
        log.info("cache.cleared")
    
    def stats(self) -> dict:
        """Return cache statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl_default": self._ttl,
        }


# ============================================
# Module-level singleton (lazy initialization)
# ============================================

_cache_instance: Optional[MemoryCache] = None


def get_cache() -> MemoryCache:
    """
    Get the singleton cache instance.
    
    Only enabled when cache_enabled is True in settings.
    Returns a no-op wrapper when disabled.
    """
    global _cache_instance
    if _cache_instance is None:
        if settings.cache_enabled:
            _cache_instance = MemoryCache(
                maxsize=256,
                ttl=settings.cache_default_ttl,
            )
            log.info(
                "cache.initialized",
                ttl=settings.cache_default_ttl,
                maxsize=256,
            )
        else:
            _cache_instance = _DisabledCache()
            log.debug("cache.disabled")
    return _cache_instance


def invalidate_cache(*keys: str) -> None:
    """
    Invalidate specific cache keys.
    
    Convenience function that gets the cache and deletes the given keys.
    """
    cache = get_cache()
    for key in keys:
        # Skip if cache is disabled
        if isinstance(cache, _DisabledCache):
            return
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(cache.delete(key))
        except RuntimeError:
            # No running loop (sync context)
            pass


# ============================================
# Disabled Cache (no-op)
# ============================================

class _DisabledCache(CacheProtocol):
    """No-op cache used when cache_enabled=False."""
    
    async def get(self, key: str) -> Optional[Any]:
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        pass
    
    async def delete(self, key: str) -> None:
        pass
    
    async def clear(self) -> None:
        pass
    
    def stats(self) -> dict:
        return {
            "enabled": False,
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "total_requests": 0,
            "hit_rate_percent": 0.0,
            "size": 0,
        }
