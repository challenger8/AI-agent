"""
services/moe/cache_service.py
-----------------------------
Caching service for MoE system.
REFACTORED: Now uses the unified cache base class.
"""

from typing import Any, Dict, Optional

from services.cache.memory_cache import MemoryCache
from services.cache.base_cache import CacheKeyBuilder
from config.moe_settings import MoESettings
from utils.logging_config import get_logger


class CacheService(MemoryCache):
    """
    LRU cache with TTL support for MoE results.

    REFACTORED: Inherits from MemoryCache to eliminate code duplication.
    Maintains backward compatibility with existing code.
    """

    def __init__(self, max_size: int = None, default_ttl: int = None):
        """
        Initialize cache service.

        Args:
            max_size: Maximum cache entries (default from MoESettings)
            default_ttl: Default TTL in seconds (default from MoESettings)
        """
        super().__init__(
            max_size=max_size or MoESettings.MAX_CACHE_SIZE,
            default_ttl=default_ttl or MoESettings.CACHE_TTL
        )
        self.logger = get_logger(self.__class__.__name__)


class ExpertResultCache(CacheService):
    """Specialized cache for expert results"""

    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)

    def cache_result(
        self,
        query: str,
        expert_type: str,
        result: Any,
        context: Dict = None
    ):
        """
        Cache expert result.

        Args:
            query: Input query
            expert_type: Type of expert
            result: Expert result
            context: Query context
        """
        key = CacheKeyBuilder.build("moe", query, expert_type, context or {})

        # Expert-specific TTL
        ttl = MoESettings.EXPERT_TIMEOUTS.get(expert_type, self.default_ttl) * 30

        self.set(key, result, ttl)
        self.logger.debug(f"Cached result for {expert_type}: {query[:30]}...")

    def get_result(
        self,
        query: str,
        expert_type: str,
        context: Dict = None
    ) -> Optional[Any]:
        """
        Get cached expert result.

        Args:
            query: Input query
            expert_type: Type of expert
            context: Query context

        Returns:
            Cached result or None
        """
        key = CacheKeyBuilder.build("moe", query, expert_type, context or {})
        return self.get(key)

    def invalidate_expert(self, expert_type: str):
        """
        Invalidate all cached results for an expert.

        Args:
            expert_type: Type of expert
        """
        # Use pattern matching from base class
        deleted = self.delete_pattern(f"*{expert_type}*")
        self.logger.info(f"Invalidated {deleted} entries for {expert_type}")


class RoutingCache(CacheService):
    """Specialized cache for routing decisions"""

    def __init__(self):
        super().__init__(default_ttl=600)  # 10 minute TTL for routing
        self.logger = get_logger(self.__class__.__name__)

    def cache_decision(self, query: str, context: Dict, decision: Any):
        """
        Cache routing decision.

        Args:
            query: Input query
            context: Query context
            decision: Routing decision
        """
        key = CacheKeyBuilder.build("moe", query, context or {})
        self.set(key, decision)

    def get_decision(self, query: str, context: Dict) -> Optional[Any]:
        """
        Get cached routing decision.

        Args:
            query: Input query
            context: Query context

        Returns:
            Cached decision or None
        """
        key = CacheKeyBuilder.build("moe", query, context or {})
        return self.get(key)
