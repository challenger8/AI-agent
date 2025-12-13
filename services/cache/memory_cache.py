"""
services/cache/memory_cache.py
------------------------------
In-memory LRU cache implementation.
Replaces duplicate cache implementations in services/moe/cache_service.py
"""

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock
from typing import Any, Dict, Optional
import logging

from services.cache.base_cache import BaseCacheInterface, CacheStats, CacheKeyBuilder

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL support"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: Optional[int] = None  # None means no expiration

    @property
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update access time and count"""
        self.last_accessed = time.time()
        self.access_count += 1


class MemoryCache(BaseCacheInterface):
    """
    Thread-safe in-memory LRU cache with TTL support.

    Features:
    - LRU eviction when max_size reached
    - Optional TTL per entry
    - Thread-safe operations
    - Statistics tracking

    This replaces the duplicate CacheService in services/moe/cache_service.py
    """

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = None
    ):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        self._stats = CacheStats()
        self.logger = logging.getLogger(self.__class__.__name__)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            if key not in self._cache:
                self._stats.record_miss()
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats.record_expiration()
                self._stats.record_miss()
                return None

            # Update access info and move to end (most recently used)
            entry.touch()
            self._cache.move_to_end(key)

            self._stats.record_hit()
            return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        with self._lock:
            ttl = ttl if ttl is not None else self.default_ttl
            now = time.time()

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl=ttl
            )

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Evict if necessary
            while len(self._cache) >= self.max_size:
                self._evict_lru()

            self._cache[key] = entry
            self._stats.record_write()
            return True

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats.record_delete()
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired"""
        with self._lock:
            if key not in self._cache:
                return False

            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                self._stats.record_expiration()
                return False

            return True

    def clear(self) -> bool:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self.logger.info("Cache cleared")
            return True

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            stats = self._stats.to_dict()
            stats['size'] = len(self._cache)
            stats['max_size'] = self.max_size
            return stats

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.record_eviction()
            self.logger.debug(f"Evicted LRU entry: {oldest_key[:30]}...")

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern with * wildcard (e.g., "deal:*")

        Returns:
            Number of keys deleted
        """
        import re
        with self._lock:
            regex_pattern = pattern.replace('*', '.*')
            keys_to_delete = [
                k for k in self._cache.keys()
                if re.match(f"^{regex_pattern}$", k)
            ]

            for key in keys_to_delete:
                del self._cache[key]
                self._stats.record_delete()

            if keys_to_delete:
                self.logger.debug(f"Deleted {len(keys_to_delete)} keys matching '{pattern}'")

            return len(keys_to_delete)

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]

            for key in expired_keys:
                del self._cache[key]
                self._stats.record_expiration()

            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def reset_stats(self):
        """Reset statistics"""
        self._stats.reset()

    # Key generation methods (for compatibility)
    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """Generate cache key"""
        return CacheKeyBuilder.simple("cache", *args)

    @staticmethod
    def hash_text(text: str) -> str:
        """Generate hash for text"""
        return CacheKeyBuilder.for_text(text)


class LRUCache(MemoryCache):
    """
    Alias for MemoryCache.

    Provides backward compatibility with existing code.
    """
    pass


# Factory function for creating cache instances
def create_memory_cache(
    max_size: int = 1000,
    default_ttl: Optional[int] = None
) -> MemoryCache:
    """
    Create a new memory cache instance.

    Args:
        max_size: Maximum number of entries
        default_ttl: Default TTL in seconds

    Returns:
        MemoryCache instance
    """
    return MemoryCache(max_size=max_size, default_ttl=default_ttl)
