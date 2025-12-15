"""
services/cache/factory.py
--------------------------
Factory functions for creating cache instances.

Extracted from cache_service.py for better modularity.
"""

from typing import Optional

from .redis_cache import CacheService
from .two_level_cache import TwoLevelCache

# Global cache instance (singleton)
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """
    Get global cache service instance (singleton)

    Returns:
        CacheService instance
    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def get_two_level_cache(l1_size: int = 100) -> TwoLevelCache:
    """
    Get two-level cache instance (L1 + L2)

    Args:
        l1_size: Maximum size of L1 (in-memory) cache

    Returns:
        TwoLevelCache instance

    Usage:
        cache = get_two_level_cache(l1_size=100)
        cache.get('key')
        cache.set('key', value, ttl=300)
    """
    redis_cache = get_cache_service()
    return TwoLevelCache(redis_cache, l1_max_size=l1_size)


def clear_cache_service() -> None:
    """Clear global cache service instance"""
    global _cache_service
    if _cache_service:
        _cache_service.close()
        _cache_service = None
