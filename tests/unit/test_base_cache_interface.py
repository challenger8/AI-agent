"""
tests/unit/test_base_cache_interface.py
----------------------------------------
Base test class for all cache interface implementations.

DRY: Consolidates duplicate cache tests from:
- test_cache_service.py (Redis cache)
- test_moe_cache.py (MoE memory cache)
- test_memory_cache.py (Generic memory cache)

Any class implementing BaseCacheInterface should pass these tests.
"""

import pytest
import time
from abc import ABC, abstractmethod


class BaseCacheInterfaceTests(ABC):
    """
    Base test class for all cache implementations.

    Subclass this and implement the cache() fixture to test
    any cache implementation against the standard interface.

    DRY: Reduces ~40 duplicate tests across 3 files to single source of truth.
    """

    @pytest.fixture
    @abstractmethod
    def cache(self):
        """
        Override in subclass to provide cache instance.

        Must return an object implementing BaseCacheInterface:
        - get(key) -> value or None
        - set(key, value, ttl=None) -> bool
        - delete(key) -> bool
        - exists(key) -> bool
        - clear() -> bool
        - get_stats() -> dict
        """
        raise NotImplementedError("Subclass must implement cache() fixture")

    # ========================================================================
    # CORE INTERFACE TESTS - All implementations must pass
    # ========================================================================

    def test_set_and_get(self, cache):
        """Test basic set and get operations"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self, cache):
        """Test getting non-existent key returns None"""
        assert cache.get("nonexistent_key_xyz_123") is None

    def test_exists(self, cache):
        """Test checking if key exists"""
        cache.set("test_exists", "value")
        assert cache.exists("test_exists") is True
        assert cache.exists("nonexistent_key") is False

    def test_delete(self, cache):
        """Test deleting key"""
        cache.set("delete_key", "value")
        assert cache.delete("delete_key") is True
        assert cache.get("delete_key") is None

    def test_delete_missing(self, cache):
        """Test deleting missing key"""
        assert cache.delete("nonexistent_key") is False

    def test_clear(self, cache):
        """Test clearing all cache entries"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_get_stats(self, cache):
        """Test getting cache statistics"""
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.get_stats()
        assert isinstance(stats, dict)
        # At minimum should have some stats (hits, misses, or size)
        assert len(stats) > 0

    def test_set_multiple_keys(self, cache):
        """Test setting multiple keys"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_overwrite_existing_key(self, cache):
        """Test overwriting existing key"""
        cache.set("key1", "old_value")
        cache.set("key1", "new_value")
        assert cache.get("key1") == "new_value"

    def test_cache_different_data_types(self, cache):
        """Test caching different data types"""
        # String
        cache.set("string_key", "string_value")
        assert cache.get("string_key") == "string_value"

        # Integer
        cache.set("int_key", 42)
        assert cache.get("int_key") == 42

        # List
        cache.set("list_key", [1, 2, 3])
        assert cache.get("list_key") == [1, 2, 3]

        # Dict
        cache.set("dict_key", {"a": 1, "b": 2})
        assert cache.get("dict_key") == {"a": 1, "b": 2}

    # ========================================================================
    # TTL TESTS - Implementations that support TTL should pass these
    # ========================================================================

    def test_ttl_expiration(self, cache):
        """Test that entries with TTL expire"""
        # Set with short TTL
        cache.set("ttl_key", "value", ttl=1)

        # Should exist immediately
        assert cache.get("ttl_key") == "value"

        # Wait for expiration
        time.sleep(1.1)

        # Should be gone
        assert cache.get("ttl_key") is None

    def test_custom_ttl(self, cache):
        """Test setting custom TTL"""
        cache.set("custom_ttl", "value", ttl=60)
        assert cache.exists("custom_ttl") is True

    # ========================================================================
    # STATS TESTS - For implementations that track statistics
    # ========================================================================

    def test_hit_rate_calculation(self, cache):
        """Test hit rate statistics"""
        cache.set("key1", "value1")

        # Generate some hits and misses
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("nonexistent")  # miss

        stats = cache.get_stats()

        # Should have hit tracking
        if 'hits' in stats:
            assert stats['hits'] == 2
            assert stats['misses'] == 1

    def test_reset_stats(self, cache):
        """Test resetting statistics"""
        # Only test if reset_stats method exists
        if hasattr(cache, 'reset_stats'):
            cache.set("key1", "value1")
            cache.get("key1")
            cache.reset_stats()

            stats = cache.get_stats()
            if 'hits' in stats:
                assert stats['hits'] == 0

    # ========================================================================
    # PATTERN DELETION TESTS - For implementations that support patterns
    # ========================================================================

    def test_delete_pattern(self, cache):
        """Test deleting keys by pattern"""
        # Only test if delete_pattern method exists
        if hasattr(cache, 'delete_pattern'):
            cache.set("user:1:name", "Alice")
            cache.set("user:2:name", "Bob")
            cache.set("product:1:name", "Widget")

            deleted = cache.delete_pattern("user:*")
            assert deleted >= 2

            assert cache.get("user:1:name") is None
            assert cache.get("user:2:name") is None
            assert cache.get("product:1:name") == "Widget"  # Should not be deleted

    # ========================================================================
    # CLEANUP TESTS - For implementations that support manual cleanup
    # ========================================================================

    def test_cleanup_expired(self, cache):
        """Test cleaning up expired entries"""
        # Only test if cleanup_expired method exists
        if hasattr(cache, 'cleanup_expired'):
            cache.set("expire1", "value1", ttl=1)
            cache.set("expire2", "value2", ttl=1)
            cache.set("keep", "value3")  # No TTL

            time.sleep(1.1)

            removed = cache.cleanup_expired()
            assert removed >= 2
            assert cache.get("keep") == "value3"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def skip_if_not_available(cache):
    """Helper to skip test if cache is not available (e.g., Redis not running)"""
    if hasattr(cache, 'is_available') and not cache.is_available():
        pytest.skip("Cache implementation not available")
