"""
tests/unit/test_moe_cache.py
----------------------------
Unit tests for MoE cache service
"""

import pytest
import time

from services.moe.cache_service import (
    CacheService,
    CacheEntry,
    ExpertResultCache,
    RoutingCache
)


class TestCacheEntry:
    """Tests for CacheEntry"""

    def test_cache_entry_creation(self):
        """Test creating cache entry"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=300
        )
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.access_count == 0

    def test_is_expired_false(self):
        """Test entry not expired"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time(),
            last_accessed=time.time(),
            ttl=300
        )
        assert entry.is_expired is False

    def test_is_expired_true(self):
        """Test entry expired"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time() - 400,
            last_accessed=time.time() - 400,
            ttl=300
        )
        assert entry.is_expired is True

    def test_touch(self):
        """Test touch updates access"""
        entry = CacheEntry(
            key="test",
            value="value",
            created_at=time.time(),
            last_accessed=time.time() - 100
        )
        old_access = entry.last_accessed
        entry.touch()
        assert entry.last_accessed > old_access
        assert entry.access_count == 1


class TestMoECacheService:
    """Tests for MoE CacheService"""

    @pytest.fixture
    def cache(self):
        """Create cache service instance"""
        return CacheService(max_size=10, default_ttl=60)

    def test_set_and_get(self, cache):
        """Test basic set and get"""
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_missing_key(self, cache):
        """Test getting missing key"""
        assert cache.get("nonexistent") is None

    def test_delete(self, cache):
        """Test deleting entry"""
        cache.set("key1", "value1")
        assert cache.delete("key1") is True
        assert cache.get("key1") is None

    def test_delete_missing(self, cache):
        """Test deleting missing key"""
        assert cache.delete("nonexistent") is False

    def test_clear(self, cache):
        """Test clearing cache"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.get("key1") is None
        assert cache.get("key2") is None

    def test_lru_eviction(self, cache):
        """Test LRU eviction when full"""
        # Fill cache
        for i in range(10):
            cache.set(f"key{i}", f"value{i}")

        # Add one more to trigger eviction
        cache.set("key10", "value10")

        # First key should be evicted
        assert cache.get("key0") is None
        assert cache.get("key10") == "value10"

    def test_expired_entry_returns_none(self, cache):
        """Test expired entry returns None"""
        # Use very short TTL that will expire
        cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cleanup_expired(self, cache):
        """Test cleaning up expired entries"""
        # Use very short TTL that will expire
        cache.set("key1", "value1", ttl=1)
        time.sleep(1.1)
        removed = cache.cleanup_expired()
        assert removed >= 1

    def test_get_stats(self, cache):
        """Test getting statistics"""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("nonexistent")

        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1
        assert 'hit_rate' in stats

    def test_reset_stats(self, cache):
        """Test resetting statistics"""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.reset_stats()

        stats = cache.get_stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0

    def test_generate_key(self):
        """Test key generation"""
        key1 = CacheService.generate_key("query", expert="deal")
        key2 = CacheService.generate_key("query", expert="deal")
        key3 = CacheService.generate_key("query", expert="sentiment")

        assert key1 == key2
        assert key1 != key3

    def test_custom_ttl(self, cache):
        """Test custom TTL per entry"""
        cache.set("short", "value", ttl=1)
        cache.set("long", "value", ttl=3600)

        time.sleep(1.1)

        assert cache.get("short") is None
        assert cache.get("long") == "value"


class TestExpertResultCache:
    """Tests for ExpertResultCache"""

    @pytest.fixture
    def expert_cache(self):
        """Create expert result cache instance"""
        return ExpertResultCache()

    def test_cache_result(self, expert_cache):
        """Test caching expert result"""
        result = {'score': 0.85, 'data': 'test'}
        expert_cache.cache_result("test query", "deal_analysis", result)

        cached = expert_cache.get_result("test query", "deal_analysis")
        assert cached == result

    def test_different_experts(self, expert_cache):
        """Test caching for different experts"""
        expert_cache.cache_result("query", "deal_analysis", {'type': 'deal'})
        expert_cache.cache_result("query", "sentiment", {'type': 'sentiment'})

        deal = expert_cache.get_result("query", "deal_analysis")
        sentiment = expert_cache.get_result("query", "sentiment")

        assert deal['type'] == 'deal'
        assert sentiment['type'] == 'sentiment'

    def test_context_affects_key(self, expert_cache):
        """Test context changes cache key"""
        expert_cache.cache_result("query", "deal", {'v': 1}, context={'deal_id': 1})
        expert_cache.cache_result("query", "deal", {'v': 2}, context={'deal_id': 2})

        r1 = expert_cache.get_result("query", "deal", context={'deal_id': 1})
        r2 = expert_cache.get_result("query", "deal", context={'deal_id': 2})

        assert r1['v'] == 1
        assert r2['v'] == 2


class TestRoutingCache:
    """Tests for RoutingCache"""

    @pytest.fixture
    def routing_cache(self):
        """Create routing cache instance"""
        return RoutingCache()

    def test_cache_decision(self, routing_cache):
        """Test caching routing decision"""
        decision = {'experts': ['deal'], 'confidence': 0.9}
        routing_cache.cache_decision("test query", {}, decision)

        cached = routing_cache.get_decision("test query", {})
        assert cached == decision

    def test_context_affects_decision(self, routing_cache):
        """Test context changes cached decision"""
        routing_cache.cache_decision("query", {'type': 'a'}, {'v': 1})
        routing_cache.cache_decision("query", {'type': 'b'}, {'v': 2})

        d1 = routing_cache.get_decision("query", {'type': 'a'})
        d2 = routing_cache.get_decision("query", {'type': 'b'})

        assert d1['v'] == 1
        assert d2['v'] == 2

    def test_default_ttl(self, routing_cache):
        """Test routing cache has longer default TTL"""
        assert routing_cache.default_ttl == 600
