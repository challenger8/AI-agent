"""
services/cache_service.py
-------------------------
Redis caching service for performance optimization
"""

import os
import json
import logging
from typing import Any, Optional, Union
from datetime import timedelta
from collections import OrderedDict
from utils.logging_config import get_logger

import threading
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not installed. Caching will be disabled.")

from utils.exceptions import ServiceError
from services.cache.base_cache import CacheKeyBuilder, generate_cache_key

class CacheService:
    """
    Redis cache service with graceful fallback
    
    Features:
    - Automatic serialization/deserialization
    - TTL (time-to-live) support
    - Pattern-based deletion
    - Graceful degradation if Redis unavailable
    - Connection pooling
    """
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 db: int = 0,
                 password: str = None,
                 enabled: bool = True):
        """
        Initialize cache service
        
        Args:
            host: Redis host (default from env or 'localhost')
            port: Redis port (default from env or 6379)
            db: Redis database number
            password: Redis password (if required)
            enabled: Enable/disable caching
        """
        self.logger = logging.getLogger(__name__)
        self.enabled = enabled and REDIS_AVAILABLE
        self.redis_client = None
        self._connection_error_logged = False
        
        if not REDIS_AVAILABLE:
            self.logger.warning("Redis library not available. Install with: pip install redis")
            self.enabled = False
            return
        
        if not self.enabled:
            self.logger.info("Caching is disabled")
            return
        
        # Get configuration from environment or use defaults
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', '6379'))
        self.db = db
        self.password = password or os.getenv('REDIS_PASSWORD')
        
        # Initialize Redis connection
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with connection pooling"""
        if not self.enabled:
            return
        
        try:
            # Create connection pool
            pool = redis.ConnectionPool(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                max_connections=10
            )
            
            self.redis_client = redis.Redis(connection_pool=pool)
            
            # Test connection
            self.redis_client.ping()
            self.logger.info(f"Redis connected: {self.host}:{self.port} (db={self.db})")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}")
            self.enabled = False
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                self.logger.debug(f"Cache MISS: {key}")
                return None
            
            self.logger.debug(f"Cache HIT: {key}")
            
            # Deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                # Return as string if not JSON
                return value
                
        except Exception as e:
            if not self._connection_error_logged:
                self.logger.error(f"Cache get error: {e}")
                self._connection_error_logged = True
            return None
    
    def set(self, 
            key: str, 
            value: Any, 
            ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (int) or timedelta
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # Serialize value to JSON
            try:
                serialized = json.dumps(value)
            except (TypeError, ValueError):
                # Fallback to string
                serialized = str(value)
            
            # Set with or without TTL
            if ttl:
                self.redis_client.setex(key, ttl, serialized)
            else:
                self.redis_client.set(key, serialized)
            
            self.logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            if not self._connection_error_logged:
                self.logger.error(f"Cache set error: {e}")
                self._connection_error_logged = True
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            self.logger.debug(f"Cache DELETE: {key}")
            return result > 0
            
        except Exception as e:
            self.logger.error(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "sentiment:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                self.logger.debug(f"Cache DELETE pattern: {pattern} ({deleted} keys)")
                return deleted
            return 0
            
        except Exception as e:
            self.logger.error(f"Cache delete pattern error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            key: Cache key
            
        Returns:
            True if exists, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            self.logger.error(f"Cache exists error: {e}")
            return False
    
    def clear_all(self) -> bool:
        """
        Clear all keys in current database
        
        Warning: Use with caution!
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            self.logger.warning("Cache cleared (all keys deleted)")
            return True
            
        except Exception as e:
            self.logger.error(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {
                "enabled": False,
                "available": False
            }
        
        try:
            info = self.redis_client.info()
            
            return {
                "enabled": True,
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_keys": self.redis_client.dbsize(),
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {
                "enabled": True,
                "available": False,
                "error": str(e)
            }
    
    @staticmethod
    def _calculate_hit_rate(hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    @staticmethod
    def generate_key(*parts: str) -> str:
        """
        Generate cache key from parts
        
        Args:
            *parts: Key parts to join
            
        Returns:
            Formatted cache key
            
        Example:
            generate_key("sentiment", "text", "abc123")
            -> "sentiment:text:abc123"
        """
        return ":".join(str(p) for p in parts)
    
    @staticmethod
    def hash_text(text: str) -> str:
        """
        Generate hash for text (useful for cache keys).
        Delegates to CacheKeyBuilder.for_text().

        Args:
            text: Text to hash

        Returns:
            MD5 hash of text
        """
        return CacheKeyBuilder.for_text(text)
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment counter
        
        Args:
            key: Counter key
            amount: Amount to increment
            
        Returns:
            New value or None
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return self.redis_client.incrby(key, amount)
        except Exception as e:
            self.logger.error(f"Cache increment error: {e}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get time-to-live for key
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no expiry, -2 if key doesn't exist
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            self.logger.error(f"Cache get TTL error: {e}")
            return None
    
    def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                self.redis_client.close()
                self.logger.info("Redis connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Redis connection: {e}")

# Global cache instance
_cache_service = None
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
    
    def get(self, key: str):
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
    
    def set(self, key: str, value, ttl=None) -> bool:
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
    
    def _set_l1(self, key: str, value):
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
        import re
        regex_pattern = pattern.replace('*', '.*')
        return re.match(f"^{regex_pattern}$", key) is not None
    
    def invalidate_deal_cache(self, deal_id: str):
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
    
    def clear_stats(self):
        """Reset statistics"""
        self.stats = {
            'l1_hits': 0,
            'l2_hits': 0,
            'misses': 0
        }
    
    # Pass-through methods for compatibility
    def generate_key(self, *parts):
        """Generate cache key (delegate to Redis cache)"""
        return self.redis_cache.generate_key(*parts)
    
    def is_available(self) -> bool:
        """Check if cache is available"""
        return self.redis_cache.is_available()
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

def clear_cache_service():
    """Clear global cache service instance"""
    global _cache_service
    if _cache_service:
        _cache_service.close()
        _cache_service = None