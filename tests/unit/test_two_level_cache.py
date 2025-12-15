"""
tests/unit/test_two_level_cache.py
----------------------------------
Tests for two-level caching system
"""

import pytest
from services.cache import CacheService, TwoLevelCache


@pytest.mark.unit
class TestTwoLevelCache:
    """Test two-level cache functionality"""
    
    @pytest.fixture
    def redis_cache(self):
        """Create Redis cache instance"""
        return CacheService(enabled=True)
    
    @pytest.fixture
    def two_level_cache(self, redis_cache):
        """Create two-level cache instance"""
        return TwoLevelCache(redis_cache, l1_max_size=10)
    
    def test_l1_cache_hit(self, two_level_cache):
        """Test L1 cache hit (in-memory)"""
        # Set value
        two_level_cache.set('test_key', 'test_value', ttl=300)
        
        # First get - should hit L1
        value = two_level_cache.get('test_key')
        assert value == 'test_value'
        
        # Check stats - should be L1 hit
        stats = two_level_cache.get_stats()
        assert stats['l1_hits'] >= 1
    
    def test_l2_cache_hit(self, two_level_cache, redis_cache):
        """Test L2 cache hit (Redis) when L1 misses"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available")
        
        # Set in L2 only
        redis_cache.set('l2_key', 'l2_value', ttl=300)
        
        # Get - should miss L1, hit L2
        value = two_level_cache.get('l2_key')
        assert value == 'l2_value'
        
        # Check stats
        stats = two_level_cache.get_stats()
        assert stats['l2_hits'] >= 1
        
        # Next get should hit L1 (promoted)
        two_level_cache.clear_stats()
        value2 = two_level_cache.get('l2_key')
        assert value2 == 'l2_value'
        stats2 = two_level_cache.get_stats()
        assert stats2['l1_hits'] == 1
    
    def test_cache_miss(self, two_level_cache):
        """Test cache miss in both levels"""
        value = two_level_cache.get('nonexistent_key')
        assert value is None
        
        stats = two_level_cache.get_stats()
        assert stats['misses'] >= 1
    
    def test_l1_lru_eviction(self, two_level_cache, redis_cache):
        """Test L1 LRU eviction when full"""
        if not redis_cache.is_available():
            pytest.skip("Redis not available - test requires L2 cache")

        # Fill L1 beyond capacity (max_size = 10)
        for i in range(15):
            two_level_cache.set(f'key_{i}', f'value_{i}')

        # L1 should only have 10 entries (most recent)
        stats = two_level_cache.get_stats()
        assert stats['l1_size'] == 10

        # Oldest keys should be evicted from L1
        # But still in L2
        value = two_level_cache.get('key_0')  # Should hit L2
        stats = two_level_cache.get_stats()
        # Could be L1 or L2 hit depending on eviction
        assert value == 'value_0'
    
    def test_delete_from_both_levels(self, two_level_cache):
        """Test delete removes from both L1 and L2"""
        two_level_cache.set('delete_test', 'value')
        
        # Verify it's cached
        assert two_level_cache.get('delete_test') == 'value'
        
        # Delete
        two_level_cache.delete('delete_test')
        
        # Should be gone
        assert two_level_cache.get('delete_test') is None
    
    def test_delete_pattern(self, two_level_cache):
        """Test pattern deletion from both levels"""
        # Set multiple keys
        two_level_cache.set('test:key1', 'value1')
        two_level_cache.set('test:key2', 'value2')
        two_level_cache.set('other:key', 'value3')
        
        # Delete pattern
        deleted = two_level_cache.delete_pattern('test:*')
        
        # test:* keys should be gone
        assert two_level_cache.get('test:key1') is None
        assert two_level_cache.get('test:key2') is None
        
        # other:key should remain
        assert two_level_cache.get('other:key') == 'value3'
    
    def test_hit_rate_calculation(self, two_level_cache):
        """Test hit rate statistics"""
        # Set some values
        two_level_cache.set('key1', 'value1')
        two_level_cache.set('key2', 'value2')
        
        # Generate hits and misses
        two_level_cache.get('key1')  # L1 hit
        two_level_cache.get('key2')  # L1 hit
        two_level_cache.get('key3')  # miss
        
        stats = two_level_cache.get_stats()
        
        assert stats['total_requests'] == 3
        assert stats['l1_hits'] == 2
        assert stats['misses'] == 1
        assert stats['overall_hit_rate'] == pytest.approx(66.67, rel=0.1)


@pytest.mark.unit
class TestTwoLevelCacheIntegration:
    """Test two-level cache with realistic usage patterns"""
    
    def test_multiple_users_same_data(self):
        """Simulate multiple users accessing same cached data"""
        redis_cache = CacheService(enabled=True)
        cache = TwoLevelCache(redis_cache, l1_max_size=50)
        
        # User 1 analyzes deal (cache miss, sets cache)
        cache.set('deal:123', {'health_score': 75}, ttl=300)
        
        # User 2-5 analyze same deal (L1 hits)
        for i in range(2, 6):
            result = cache.get('deal:123')
            assert result['health_score'] == 75
        
        stats = cache.get_stats()
        
        # Should have mostly L1 hits
        assert stats['l1_hits'] >= 4
        assert stats['l1_hit_rate'] > 80  # >80% L1 hit rate