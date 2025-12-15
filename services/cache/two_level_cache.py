"""
services/cache/two_level_cache.py
----------------------------------
Two-level caching: L1 (in-memory) + L2 (Redis)

Extracted from cache_service.py for better modularity.
"""

import re
import threading
from collections import OrderedDict
from typing import Any, Optional

from utils.logging_config import get_logger
from .redis_cache import CacheService


class TwoLevelCache:
    """
    Two-level caching: L1 (in-memory) + L2 (Redis)

    L1: Fast in-memory LRU cache (limited size, no TTL)
    L2: Larger Redis cache (persistent, with TTL)

    Benefits:
    - L1 hits: ~0.5ms (1000x faster than Redis)
    - L2 hits: ~5ms (network call)
    - Reduces Redis load by 80-90%
    - Better for concurrent users viewing same data
    """

    def __init__(self, redis_cache: CacheService, l1_max_size: int = 100):
        """
        Initialize two-level cache

        Args:
            redis_cache: Underlying Redis cache (L2)
            l1_max_size: Maximum entries in L1 cache (default: 100)
        """
        self.redis_cache = redis_cache  # L2
        self.l1_cache = OrderedDict()   # L1 (LRU)
        self.l1_max_size = l1_max_size
        self.lock = threading.Lock()
        self.logger = get_logger(self.__class__.__name__)

        # Statistics
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get from cache (L1 first, then L2)

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        # Try L1 first (in-memory, blazing fast)
        with self.lock:
            if key in self.l1_cache:
                self.stats['l1_hits'] += 1
                # Move to end (LRU - most recently used)
                self.l1_cache.move_to_end(key)
                value = self.l1_cache[key]
                self.logger.debug(f"L1 HIT: {key}")
                return value

        # Try L2 (Redis)
        value = self.redis_cache.get(key)
        if value is not None:
            self.stats['l2_hits'] += 1
            self.logger.debug(f"L2 HIT: {key}")
            # Promote to L1 for future fast access
            self._set_l1(key, value)
            return value

        # Cache miss
        self.stats['misses'] += 1
        self.logger.debug(f"MISS: {key}")
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set in both caches

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL for L2 (Redis only, L1 has no TTL)

        Returns:
            True if successful
        """
        # Set in L1 (no TTL, size-limited with LRU eviction)
        self._set_l1(key, value)

        # Set in L2 (with TTL)
        return self.redis_cache.set(key, value, ttl)

    def _set_l1(self, key: str, value: Any) -> None:
        """Set in L1 cache with LRU eviction"""
        with self.lock:
            if key in self.l1_cache:
                # Update existing entry and move to end
                self.l1_cache[key] = value
                self.l1_cache.move_to_end(key)
            else:
                # Add new entry
                self.l1_cache[key] = value

                # Evict oldest if full (LRU)
                if len(self.l1_cache) > self.l1_max_size:
                    oldest_key = next(iter(self.l1_cache))
                    del self.l1_cache[oldest_key]
                    self.logger.debug(f"L1 EVICT: {oldest_key}")

    def delete(self, key: str) -> bool:
        """Delete from both caches"""
        # Delete from L1
        with self.lock:
            if key in self.l1_cache:
                del self.l1_cache[key]

        # Delete from L2
        return self.redis_cache.delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """Delete pattern from both caches"""
        # Clear matching L1 entries
        with self.lock:
            keys_to_delete = [
                k for k in self.l1_cache.keys()
                if self._matches_pattern(k, pattern)
            ]
            for key in keys_to_delete:
                del self.l1_cache[key]

        # Clear L2
        return self.redis_cache.delete_pattern(pattern)

    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcard)"""
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f"^{regex_pattern}$", key) is not None

    def invalidate_deal_cache(self, deal_id: str) -> None:
        """Invalidate deal-related caches in both levels"""
        self.delete(self.generate_key("deal_analysis", deal_id))
        self.delete_pattern("portfolio:*")

    def exists(self, key: str) -> bool:
        """Check if key exists in either cache"""
        with self.lock:
            if key in self.l1_cache:
                return True
        return self.redis_cache.exists(key)

    def get_stats(self) -> dict:
        """
        Get cache statistics

        Returns:
            Dictionary with L1/L2 hit rates and sizes
        """
        total = self.stats['l1_hits'] + self.stats['l2_hits'] + self.stats['misses']

        stats = {
            'l1_hits': self.stats['l1_hits'],
            'l2_hits': self.stats['l2_hits'],
            'misses': self.stats['misses'],
            'total_requests': total,
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.l1_max_size
        }

        if total > 0:
            stats['l1_hit_rate'] = round((self.stats['l1_hits'] / total) * 100, 2)
            stats['l2_hit_rate'] = round((self.stats['l2_hits'] / total) * 100, 2)
            stats['overall_hit_rate'] = round(((self.stats['l1_hits'] + self.stats['l2_hits']) / total) * 100, 2)
        else:
            stats['l1_hit_rate'] = 0.0
            stats['l2_hit_rate'] = 0.0
            stats['overall_hit_rate'] = 0.0

        return stats

    def clear_stats(self) -> None:
        """Reset statistics"""
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0
        }

    # Pass-through methods for compatibility
    def generate_key(self, *parts: str) -> str:
        """
        Generate cache key.

        REFACTORED: Now uses CacheKeyBuilder.build() for consistency.
        """
        from services.cache.base_cache import CacheKeyBuilder
        if not parts:
            return ""
        prefix = str(parts[0]) if parts else ""
        remaining = parts[1:] if len(parts) > 1 else ()
        return CacheKeyBuilder.build(prefix, *remaining) if parts else ""

    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.redis_cache.is_available()
