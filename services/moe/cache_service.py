"""
services/moe/cache_service.py
-----------------------------
Caching service for MoE system with TTL and LRU eviction
"""

import hashlib
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from threading import Lock

from config.moe_settings import MoESettings
from utils.logging_config import get_logger


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    last_accessed: float
    access_count: int = 0
    ttl: int = 300

    @property
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        return time.time() - self.created_at > self.ttl

    def touch(self):
        """Update last accessed time"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheService:
    """LRU cache with TTL support for MoE results"""

    def __init__(self, max_size: int = None, default_ttl: int = None):
        """
        Initialize cache service

        Args:
            max_size: Maximum cache entries
            default_ttl: Default TTL in seconds
        """
        self.logger = get_logger(self.__class__.__name__)
        self.max_size = max_size or MoESettings.MAX_CACHE_SIZE
        self.default_ttl = default_ttl or MoESettings.CACHE_TTL

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()

        # Statistics
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_writes': 0
        }

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None

            entry = self._cache[key]

            # Check expiration
            if entry.is_expired:
                del self._cache[key]
                self._stats['expirations'] += 1
                self._stats['misses'] += 1
                return None

            # Update access
            entry.touch()

            # Move to end (most recently used)
            self._cache.move_to_end(key)

            self._stats['hits'] += 1
            return entry.value

    def set(self, key: str, value: Any, ttl: int = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        with self._lock:
            ttl = ttl or self.default_ttl
            now = time.time()

            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                ttl=ttl
            )

            # Remove if exists (to update position)
            if key in self._cache:
                del self._cache[key]

            # Evict if necessary
            while len(self._cache) >= self.max_size:
                self._evict_lru()

            self._cache[key] = entry
            self._stats['total_writes'] += 1

    def delete(self, key: str) -> bool:
        """
        Delete entry from cache

        Args:
            key: Cache key

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def _evict_lru(self):
        """Evict least recently used entry"""
        if self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
            self.logger.debug(f"Evicted LRU entry: {oldest_key[:20]}...")

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
        self.logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """
        Remove expired entries

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
                self._stats['expirations'] += 1

            if expired_keys:
                self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0.0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self._stats['evictions'],
                'expirations': self._stats['expirations'],
                'total_writes': self._stats['total_writes']
            }

    def reset_stats(self):
        """Reset statistics"""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0,
            'total_writes': 0
        }

    @staticmethod
    def generate_key(*args, **kwargs) -> str:
        """
        Generate cache key from arguments

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash key
        """
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)
        return hashlib.sha256(key_str.encode()).hexdigest()


class ExpertResultCache(CacheService):
    """Specialized cache for expert results"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    def cache_result(self, query: str, expert_type: str, result: Any, context: Dict = None):
        """
        Cache expert result

        Args:
            query: Input query
            expert_type: Type of expert
            result: Expert result
            context: Query context
        """
        key = self.generate_key(query, expert_type, context or {})

        # Expert-specific TTL
        ttl = MoESettings.EXPERT_TIMEOUTS.get(expert_type, self.default_ttl) * 30

        self.set(key, result, ttl)
        self.logger.debug(f"Cached result for {expert_type}: {query[:30]}...")

    def get_result(self, query: str, expert_type: str, context: Dict = None) -> Optional[Any]:
        """
        Get cached expert result

        Args:
            query: Input query
            expert_type: Type of expert
            context: Query context

        Returns:
            Cached result or None
        """
        key = self.generate_key(query, expert_type, context or {})
        return self.get(key)

    def invalidate_expert(self, expert_type: str):
        """
        Invalidate all cached results for an expert

        Args:
            expert_type: Type of expert
        """
        with self._lock:
            keys_to_delete = [
                key for key in self._cache.keys()
                if expert_type in key
            ]

            for key in keys_to_delete:
                del self._cache[key]

            self.logger.info(f"Invalidated {len(keys_to_delete)} entries for {expert_type}")


class RoutingCache(CacheService):
    """Specialized cache for routing decisions"""

    def __init__(self):
        super().__init__(default_ttl=600)  # 10 minute TTL for routing
        self.logger = get_logger(self.__class__.__name__)

    def cache_decision(self, query: str, context: Dict, decision: Any):
        """
        Cache routing decision

        Args:
            query: Input query
            context: Query context
            decision: Routing decision
        """
        key = self.generate_key(query, context or {})
        self.set(key, decision)

    def get_decision(self, query: str, context: Dict) -> Optional[Any]:
        """
        Get cached routing decision

        Args:
            query: Input query
            context: Query context

        Returns:
            Cached decision or None
        """
        key = self.generate_key(query, context or {})
        return self.get(key)
