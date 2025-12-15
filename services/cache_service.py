"""
services/cache_service.py
-------------------------
DEPRECATED: This file is kept for backward compatibility.

Use the modular cache package instead:
    from services.cache import CacheService, TwoLevelCache
    from services.cache import get_cache_service, get_two_level_cache

Refactored into modular structure:
- services/cache/base_cache.py - Base interfaces and key builder
- services/cache/redis_cache.py - Redis cache implementation (CacheService)
- services/cache/two_level_cache.py - Two-level caching (L1+L2)
- services/cache/factory.py - Factory functions
- services/cache/__init__.py - Public API exports
"""

# Import everything from the modular structure for backward compatibility
from services.cache.redis_cache import CacheService
from services.cache.two_level_cache import TwoLevelCache
from services.cache.base_cache import CacheKeyBuilder, generate_cache_key
from services.cache.factory import (
    get_cache_service,
    get_two_level_cache,
    clear_cache_service
)

# Re-export for backward compatibility
__all__ = [
    'CacheService',
    'TwoLevelCache',
    'CacheKeyBuilder',
    'generate_cache_key',
    'get_cache_service',
    'get_two_level_cache',
    'clear_cache_service',
]
