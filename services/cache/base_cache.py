"""
services/cache/base_cache.py
----------------------------
Abstract base class for cache implementations.
DRY/SOLID: Single interface for all cache types.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from datetime import timedelta
import hashlib
import logging

logger = logging.getLogger(__name__)


class BaseCacheInterface(ABC):
    """
    Abstract base class defining the cache interface.

    All cache implementations must implement these methods.

    SOLID Principles:
    - ISP: Minimal interface with essential methods only
    - LSP: All implementations are interchangeable
    - DIP: Depend on this abstraction, not concrete implementations
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        pass


class CacheKeyBuilder:
    """
    Utility class for building cache keys.

    Provides consistent key generation across all cache implementations.
    """

    SEPARATOR = ":"

    @classmethod
    def simple(cls, prefix: str, *parts) -> str:
        """
        Build simple cache key from parts.

        Args:
            prefix: Key prefix (e.g., 'deal', 'sentiment')
            *parts: Additional key parts

        Returns:
            Formatted cache key

        Example:
            >>> CacheKeyBuilder.simple('deal', '123', 'analysis')
            'deal:123:analysis'
        """
        all_parts = [prefix] + [str(p) for p in parts if p is not None]
        return cls.SEPARATOR.join(all_parts)

    @classmethod
    def hashed(cls, prefix: str, data: Any) -> str:
        """
        Build cache key with hashed data.

        Args:
            prefix: Key prefix
            data: Data to hash (string, dict, or any serializable)

        Returns:
            Cache key with hash suffix

        Example:
            >>> CacheKeyBuilder.hashed('query', 'some long query text')
            'query:a1b2c3d4e5f6...'
        """
        if isinstance(data, dict):
            data_str = str(sorted(data.items()))
        else:
            data_str = str(data)

        hash_value = hashlib.md5(data_str.encode()).hexdigest()[:16]
        return f"{prefix}{cls.SEPARATOR}{hash_value}"

    @classmethod
    def for_text(cls, text: str) -> str:
        """
        Generate hash key for text content.

        Args:
            text: Text to hash

        Returns:
            MD5 hash of text
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    @classmethod
    def for_query(cls, prefix: str, query: str, context: Optional[Dict] = None) -> str:
        """
        Build cache key for query + context.

        Args:
            prefix: Key prefix
            query: Query string
            context: Optional context dict

        Returns:
            Cache key combining query and context
        """
        context_str = str(sorted(context.items())) if context else ""
        combined = f"{query}:{context_str}"
        return cls.hashed(prefix, combined)

    @classmethod
    def build(cls, prefix: str, *args, **kwargs) -> str:
        """
        UNIVERSAL cache key builder - consolidates all generation methods.

        DRY: Single source of truth for ALL cache key generation.
        Replaces 6 different implementations across the codebase.

        Args:
            prefix: Key prefix (e.g., 'deal', 'routing', 'search')
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            Generated cache key (hashed for complex data, simple for basic)

        Examples:
            >>> CacheKeyBuilder.build('deal', '123')
            'deal:123'

            >>> CacheKeyBuilder.build('routing', 'query text', context={'hint': 'x'})
            'routing:a1b2c3...'

            >>> CacheKeyBuilder.build('search', 'query', type='deals', n=10)
            'search:5f4d...'

        Usage:
            # Replace old patterns:
            # OLD: generate_cache_key("prefix", arg1, arg2, key=val)
            # NEW: CacheKeyBuilder.build("prefix", arg1, arg2, key=val)
        """
        # If no args/kwargs, just return prefix
        if not args and not kwargs:
            return prefix

        # Simple case: just positional args, no kwargs
        if not kwargs:
            # If all args are simple types, use simple key
            if all(isinstance(arg, (str, int, float, bool, type(None))) for arg in args):
                return cls.simple(prefix, *args)
            # Otherwise hash complex args
            return cls.hashed(prefix, args)

        # Complex case: has kwargs (need hashing)
        # Build deterministic string from args + kwargs
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        combined = ":".join(key_parts)

        # Hash if combined string is long or has complex data
        if len(combined) > 100 or any(isinstance(arg, (dict, list, tuple)) for arg in args):
            hash_value = hashlib.sha256(combined.encode()).hexdigest()[:16]
            return f"{prefix}{cls.SEPARATOR}{hash_value}"

        # Otherwise use simple key
        return f"{prefix}{cls.SEPARATOR}{combined}"


class CacheStats:
    """
    Cache statistics tracker.

    Provides consistent statistics tracking across cache implementations.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all statistics"""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'writes': 0,
            'deletes': 0,
            'evictions': 0,
            'expirations': 0
        }

    def record_hit(self):
        """Record a cache hit"""
        self._stats['hits'] += 1

    def record_miss(self):
        """Record a cache miss"""
        self._stats['misses'] += 1

    def record_write(self):
        """Record a write operation"""
        self._stats['writes'] += 1

    def record_delete(self):
        """Record a delete operation"""
        self._stats['deletes'] += 1

    def record_eviction(self):
        """Record an eviction"""
        self._stats['evictions'] += 1

    def record_expiration(self):
        """Record an expiration"""
        self._stats['expirations'] += 1

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self._stats['hits'] + self._stats['misses']
        if total == 0:
            return 0.0
        return round((self._stats['hits'] / total) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        """Get statistics as dictionary"""
        stats = self._stats.copy()
        stats['hit_rate'] = self.hit_rate
        stats['total_requests'] = self._stats['hits'] + self._stats['misses']
        return stats


# Convenience function for generating keys
def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate cache key based on input type.

    Args:
        prefix: Key prefix
        *args: Key parts
        **kwargs: If 'context' is provided, use query-style key

    Returns:
        Formatted cache key

    Examples:
        >>> generate_cache_key('deal', deal_id)
        'deal:123'

        >>> generate_cache_key('query', query, context={'deal_id': 1})
        'query:hash...'
    """
    if 'context' in kwargs:
        query = args[0] if args else ""
        return CacheKeyBuilder.for_query(prefix, query, kwargs['context'])
    return CacheKeyBuilder.simple(prefix, *args)
