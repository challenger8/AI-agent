"""
tests/unit/test_memory_cache.py
-------------------------------
Unit tests for MemoryCache and related cache classes.
"""

import pytest
import time
from services.cache.memory_cache import MemoryCache, LRUCache, create_memory_cache
from services.cache.base_cache import (
    BaseCacheInterface,
    CacheKeyBuilder,
    CacheStats,
    generate_cache_key
)


class TestCacheKeyBuilder:
    """Tests for CacheKeyBuilder utility"""

    def test_simple_single_part(self):
        """Test simple key with single part"""
        result = CacheKeyBuilder.simple('deal')
        assert result == 'deal'

    def test_simple_multiple_parts(self):
        """Test simple key with multiple parts"""
        result = CacheKeyBuilder.simple('deal', '123', 'analysis')
        assert result == 'deal:123:analysis'

    def test_simple_with_none_parts(self):
        """Test simple key ignores None parts"""
        result = CacheKeyBuilder.simple('deal', None, '123')
        assert result == 'deal:123'

    def test_hashed_with_string(self):
        """Test hashed key with string data"""
        result = CacheKeyBuilder.hashed('query', 'some long query text')
        assert result.startswith('query:')
        assert len(result) == len('query:') + 16

    def test_hashed_with_dict(self):
        """Test hashed key with dict data"""
        result = CacheKeyBuilder.hashed('context', {'a': 1, 'b': 2})
        assert result.startswith('context:')

    def test_for_text(self):
        """Test for_text generates MD5 hash"""
        result = CacheKeyBuilder.for_text('test text')
        assert len(result) == 32  # MD5 hash length

    def test_for_text_consistent(self):
        """Test for_text generates consistent hash"""
        result1 = CacheKeyBuilder.for_text('test text')
        result2 = CacheKeyBuilder.for_text('test text')
        assert result1 == result2

    def test_for_query(self):
        """Test for_query with query and context"""
        result = CacheKeyBuilder.for_query('deal', 'search query', {'filter': 'active'})
        assert result.startswith('deal:')

    def test_for_query_no_context(self):
        """Test for_query without context"""
        result = CacheKeyBuilder.for_query('deal', 'search query')
        assert result.startswith('deal:')


class TestCacheStats:
    """Tests for CacheStats tracker"""

    def test_initial_stats(self):
        """Test initial stats are zero"""
        stats = CacheStats()
        result = stats.to_dict()
        assert result['hits'] == 0
        assert result['misses'] == 0
        assert result['hit_rate'] == 0.0

    def test_record_hit(self):
        """Test recording hits"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        assert stats.to_dict()['hits'] == 2

    def test_record_miss(self):
        """Test recording misses"""
        stats = CacheStats()
        stats.record_miss()
        assert stats.to_dict()['misses'] == 1

    def test_hit_rate_calculation(self):
        """Test hit rate calculation"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_hit()
        stats.record_hit()
        stats.record_miss()
        assert stats.hit_rate == 75.0

    def test_hit_rate_zero_requests(self):
        """Test hit rate with zero requests"""
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_reset(self):
        """Test reset clears all stats"""
        stats = CacheStats()
        stats.record_hit()
        stats.record_miss()
        stats.reset()
        result = stats.to_dict()
        assert result['hits'] == 0
        assert result['misses'] == 0


class TestMemoryCache:
    """Tests for MemoryCache implementation"""

    def test_implements_interface(self):
        """Test MemoryCache implements BaseCacheInterface"""
        cache = MemoryCache()
        assert isinstance(cache, BaseCacheInterface)

    def test_set_and_get(self):
        """Test basic set and get operations"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        result = cache.get('key1')
        assert result == 'value1'

    def test_get_missing_key(self):
        """Test get returns None for missing key"""
        cache = MemoryCache()
        result = cache.get('nonexistent')
        assert result is None

    def test_delete(self):
        """Test delete operation"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        result = cache.delete('key1')
        assert result is True
        assert cache.get('key1') is None

    def test_delete_missing(self):
        """Test delete returns False for missing key"""
        cache = MemoryCache()
        result = cache.delete('nonexistent')
        assert result is False

    def test_exists(self):
        """Test exists operation"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        assert cache.exists('key1') is True
        assert cache.exists('nonexistent') is False

    def test_clear(self):
        """Test clear operation"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.clear()
        assert cache.get('key1') is None
        assert cache.get('key2') is None

    def test_lru_eviction(self):
        """Test LRU eviction when max_size reached"""
        cache = MemoryCache(max_size=3)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        # Access key1 to make it recently used
        cache.get('key1')
        # Add new key, should evict key2 (least recently used)
        cache.set('key4', 'value4')

        assert cache.exists('key1') is True  # Recently accessed
        assert cache.exists('key2') is False  # Evicted
        assert cache.exists('key3') is True
        assert cache.exists('key4') is True

    def test_ttl_expiration(self):
        """Test TTL expiration"""
        cache = MemoryCache(default_ttl=1)  # 1 second TTL
        cache.set('key1', 'value1')
        assert cache.get('key1') == 'value1'

        # Wait for expiration
        time.sleep(1.5)
        assert cache.get('key1') is None

    def test_custom_ttl(self):
        """Test custom TTL per entry"""
        cache = MemoryCache(default_ttl=10)
        cache.set('key1', 'value1', ttl=1)  # 1 second TTL
        assert cache.get('key1') == 'value1'

        time.sleep(1.5)
        assert cache.get('key1') is None

    def test_get_stats(self):
        """Test get_stats returns correct information"""
        cache = MemoryCache(max_size=100)
        cache.set('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss

        stats = cache.get_stats()
        assert stats['size'] == 1
        assert stats['max_size'] == 100
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_delete_pattern(self):
        """Test delete_pattern removes matching keys"""
        cache = MemoryCache()
        cache.set('deal:1:analysis', 'value1')
        cache.set('deal:2:analysis', 'value2')
        cache.set('activity:1:summary', 'value3')

        deleted = cache.delete_pattern('deal:*')
        assert deleted == 2
        assert cache.exists('deal:1:analysis') is False
        assert cache.exists('activity:1:summary') is True

    def test_cleanup_expired(self):
        """Test cleanup_expired removes expired entries"""
        cache = MemoryCache()
        cache.set('key1', 'value1', ttl=1)
        cache.set('key2', 'value2', ttl=10)

        time.sleep(1.5)
        removed = cache.cleanup_expired()

        assert removed == 1
        assert cache.exists('key1') is False
        assert cache.exists('key2') is True

    def test_generate_key_static(self):
        """Test static generate_key method"""
        key = MemoryCache.generate_key('deal', '123')
        assert 'deal' in key
        assert '123' in key

    def test_hash_text_static(self):
        """Test static hash_text method"""
        hash1 = MemoryCache.hash_text('test text')
        hash2 = MemoryCache.hash_text('test text')
        assert hash1 == hash2

    def test_reset_stats(self):
        """Test reset_stats clears statistics"""
        cache = MemoryCache()
        cache.set('key1', 'value1')
        cache.get('key1')
        cache.reset_stats()

        stats = cache.get_stats()
        assert stats['hits'] == 0


class TestLRUCache:
    """Tests for LRUCache alias"""

    def test_is_alias_for_memory_cache(self):
        """Test LRUCache is an alias for MemoryCache"""
        cache = LRUCache()
        assert isinstance(cache, MemoryCache)

    def test_basic_operations(self):
        """Test basic operations work"""
        cache = LRUCache()
        cache.set('key', 'value')
        assert cache.get('key') == 'value'


class TestCreateMemoryCacheFactory:
    """Tests for create_memory_cache factory function"""

    def test_creates_memory_cache(self):
        """Test factory creates MemoryCache instance"""
        cache = create_memory_cache()
        assert isinstance(cache, MemoryCache)

    def test_with_custom_params(self):
        """Test factory accepts custom parameters"""
        cache = create_memory_cache(max_size=50, default_ttl=300)
        assert cache.max_size == 50
        assert cache.default_ttl == 300


class TestGenerateCacheKeyFunction:
    """Tests for generate_cache_key convenience function"""

    def test_simple_key(self):
        """Test simple key generation"""
        key = generate_cache_key('deal', '123')
        assert 'deal' in key
        assert '123' in key

    def test_with_context(self):
        """Test key generation with context"""
        key = generate_cache_key('query', 'search', context={'filter': 'active'})
        assert key.startswith('query:')
