"""
tests/unit/test_memory_cache.py
-------------------------------
Unit tests for MemoryCache and related cache classes.

REFACTORED: Now uses BaseCacheInterfaceTests to eliminate duplication.
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
from tests.unit.test_base_cache_interface import BaseCacheInterfaceTests


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


class TestMemoryCache(BaseCacheInterfaceTests):
    """
    Tests for MemoryCache implementation.

    REFACTORED: Inherits base tests from BaseCacheInterfaceTests to eliminate
    duplication. Only memory-cache-specific tests are defined here.
    """

    @pytest.fixture
    def cache(self):
        """Provide MemoryCache instance for base tests"""
        return MemoryCache(max_size=100, default_ttl=60)

    def test_implements_interface(self):
        """Test MemoryCache implements BaseCacheInterface"""
        cache = MemoryCache()
        assert isinstance(cache, BaseCacheInterface)

    def test_lru_eviction_order(self):
        """Test LRU eviction order (memory-cache-specific behavior)"""
        cache = MemoryCache(max_size=3)
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        # Access key1 to make it recently used
        cache.get('key1')
        # Add new key, should evict key2 (least recently used)
        cache.set('key4', 'value4')

        assert cache.exists('key1') is True  # Recently accessed
        assert cache.exists('key2') is False  # Evicted (LRU)
        assert cache.exists('key3') is True
        assert cache.exists('key4') is True

    def test_get_stats_structure(self):
        """Test get_stats returns correct structure"""
        cache = MemoryCache(max_size=100)
        cache.set('key1', 'value1')
        cache.get('key1')  # Hit
        cache.get('key2')  # Miss

        stats = cache.get_stats()
        assert stats['size'] == 1
        assert stats['max_size'] == 100
        assert stats['hits'] == 1
        assert stats['misses'] == 1

    def test_generate_key_static(self):
        """Test static generate_key method (mem-cache-specific)"""
        key = MemoryCache.generate_key('deal', '123')
        assert 'deal' in key
        assert '123' in key

    def test_hash_text_static(self):
        """Test static hash_text method (mem-cache-specific)"""
        hash1 = MemoryCache.hash_text('test text')
        hash2 = MemoryCache.hash_text('test text')
        assert hash1 == hash2


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
