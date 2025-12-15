"""
services/cache/__init__.py
--------------------------
Unified cache module for Persian Deal Analyzer
"""

from services.cache.base_cache import (
    BaseCacheInterface,
    CacheKeyBuilder,
    CacheStats,
    generate_cache_key
)
from services.cache.memory_cache import MemoryCache
from services.cache.redis_cache import CacheService
from services.cache.two_level_cache import TwoLevelCache
from services.cache.factory import (
    get_cache_service,
    get_two_level_cache,
    clear_cache_service
)

__all__ = [
    # Base interfaces
    'BaseCacheInterface',
    'CacheKeyBuilder',
    'CacheStats',
    'generate_cache_key',

    # Memory cache implementations
    'MemoryCache',

    # Redis cache
    'CacheService',

    # Two-level cache
    'TwoLevelCache',

    # Factory functions
    'get_cache_service',
    'get_two_level_cache',
    'clear_cache_service',
]
