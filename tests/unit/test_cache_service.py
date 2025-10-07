"""
Unit tests for CacheService

TODO: Copy content from artifact 'test_cache_service' above.

To complete setup:
1. Find the artifact named 'test_cache_service' in the conversation above
2. Copy its entire content
3. Replace this file's content with the artifact content
"""

# Placeholder - Replace with actual content from artifact
pass
"""
tests/unit/test_cache_service.py
---------------------------------
Unit tests for CacheService
"""

import pytest
from datetime import timedelta
from services.cache_service import CacheService, get_cache_service


class TestCacheServiceBasic:
    """Test basic cache service functionality"""
    
    def test_cache_service_creation(self):
        """Test creating cache service instance"""
        cache = CacheService(enabled=True)
        
        assert cache is not None
        assert hasattr(cache, 'enabled')
    
    def test_cache_service_disabled(self):
        """Test cache service when disabled"""
        cache = CacheService(enabled=False)
        
        assert cache.enabled is False
        # Operations should not fail, just return False/None
        result = cache.set('key', 'value')
        assert result is False
    
    def test_is_available(self):
        """Test checking if cache is available"""
        cache = CacheService(enabled=True)
        
        # Result depends on Redis availability
        is_avail = cache.is_available()
        assert isinstance(is_avail, bool)


class TestCacheOperations:
    """Test cache set/get/delete operations"""
    def test_delete_key(self):
        """Test deleting a key"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set a test key
            cache.set('test_delete', 'value')
            
            # Delete the key
            success = cache.delete('test_delete')
            
            assert success is True
            
            # Verify the key is gone
            value = cache.get('test_delete')
            assert value is None
        else:
            pytest.skip("Redis not available")
    def test_set_and_get(self):
        """Test setting and getting a value"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set value
            success = cache.set('test_key', 'test_value')
            assert success is True
            
            # Get value
            value = cache.get('test_key')
            assert value == 'test_value'
        else:
            pytest.skip("Redis not available")
    
    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns None"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            value = cache.get('nonexistent_key_xyz_123')
            assert value is None
        else:
            pytest.skip("Redis not available")
    
    def test_delete_key(self):
        """Test deleting a key"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set and then delete
            cache.set('test_delete', 'value')
            success = cache.delete('test_delete')
            
            assert success is True
            
            # Verify deleted
            value = cache.get('test_delete')
            assert value is None
        else:
            pytest.skip("Redis not available")
    
    def test_exists(self):
        """Test checking if key exists"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            cache.set('test_exists', 'value')
            
            # Should exist
            assert cache.exists('test_exists') is True
            
            # Should not exist
            assert cache.exists('nonexistent_key') is False
        else:
            pytest.skip("Redis not available")
    
    def test_set_with_ttl_int(self):
        """Test setting value with TTL (integer seconds)"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            success = cache.set('test_ttl', 'value', ttl=60)
            assert success is True
            
            # Verify it exists
            assert cache.exists('test_ttl') is True
        else:
            pytest.skip("Redis not available")
    
    def test_set_with_ttl_timedelta(self):
        """Test setting value with TTL (timedelta)"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            success = cache.set('test_ttl_td', 'value', ttl=timedelta(minutes=5))
            assert success is True
            
            # Get TTL
            ttl = cache.get_ttl('test_ttl_td')
            assert ttl is not None
            assert ttl > 0
        else:
            pytest.skip("Redis not available")

class TestCacheKeyGeneration:
    """Test cache key generation utilities"""
    
    def test_generate_key(self):
        """Test generating cache keys from parts"""
        # Test with multiple parts
        key = CacheService.generate_key('sentiment', 'abc123', 'v1')
        assert key == 'sentiment:abc123:v1'
        
        # Test with two parts
        key = CacheService.generate_key('analytics', 'deal-456')
        assert key == 'analytics:deal-456'
        
        # Test with single part
        key = CacheService.generate_key('simple')
        assert key == 'simple'
        
        # Test that keys are strings
        key = CacheService.generate_key('test', '123')
        assert isinstance(key, str)
        
        # Test with numbers (converted to strings)
        key = CacheService.generate_key('count', 42)
        assert 'count' in key
        assert '42' in key
    
    def test_hash_text(self):
        """Test text hashing for consistent cache keys"""
        # Test consistency - same text produces same hash
        text = "این یک متن فارسی برای تست است"
        hash1 = CacheService.hash_text(text)
        hash2 = CacheService.hash_text(text)
        
        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) > 0
        
        # Test different texts produce different hashes
        text1 = "متن اول"
        text2 = "متن دوم"
        hash1 = CacheService.hash_text(text1)
        hash2 = CacheService.hash_text(text2)
        
        assert hash1 != hash2
        
        # Test empty string (edge case)
        hash_empty = CacheService.hash_text("")
        assert hash_empty is not None
        assert isinstance(hash_empty, str)
        
        # Test long text
        long_text = "متن طولانی " * 1000
        hash_long = CacheService.hash_text(long_text)
        assert hash_long is not None
        assert isinstance(hash_long, str)
        
        # Test English text
        english_text = "This is a test sentence"
        hash_english = CacheService.hash_text(english_text)
        assert hash_english is not None
        assert len(hash_english) > 0
class TestCacheBulkOperations:
    """Test bulk cache operations"""
    
    def test_delete_pattern(self):
        """Test deleting keys by pattern"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set up multiple keys with different prefixes
            cache.set('sentiment:abc', {'test': 1})
            cache.set('sentiment:xyz', {'test': 2})
            cache.set('sentiment:123', {'test': 3})
            cache.set('analytics:456', {'test': 4})
            
            # Delete all sentiment keys
            count = cache.delete_pattern('sentiment:*')
            
            # Should have deleted at least 3 keys
            assert count >= 3
            
            # Verify sentiment keys are gone
            assert cache.get('sentiment:abc') is None
            assert cache.get('sentiment:xyz') is None
            assert cache.get('sentiment:123') is None
            
            # Verify analytics key still exists
            analytics_value = cache.get('analytics:456')
            assert analytics_value is not None
            assert analytics_value['test'] == 4
        else:
            pytest.skip("Redis not available")
    
    def test_clear_all(self):
        """Test clearing entire cache"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set up several test keys
            cache.set('test_key_1', 'value1')
            cache.set('test_key_2', 'value2')
            cache.set('test_key_3', 'value3')
            
            # Clear all cache
            result = cache.clear_all()
            
            # Should return success
            assert result is True
            
            # Verify all keys are gone
            assert cache.get('test_key_1') is None
            assert cache.get('test_key_2') is None
            assert cache.get('test_key_3') is None
        else:
            pytest.skip("Redis not available")
class TestCacheDataTypes:
    """Test caching different data types"""
    
    def test_cache_string(self):
        """Test caching string values"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            cache.set('string_key', 'string value')
            value = cache.get('string_key')
            
            assert value == 'string value'
            assert isinstance(value, str)
        else:
            pytest.skip("Redis not available")
    
    def test_cache_dict(self):
        """Test caching dictionary values"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            test_dict = {'key1': 'value1', 'key2': 123}
            cache.set('dict_key', test_dict)
            value = cache.get('dict_key')
            
            assert value == test_dict
            assert isinstance(value, dict)
        else:
            pytest.skip("Redis not available")
    
    def test_cache_list(self):
        """Test caching list values"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            test_list = [1, 2, 3, 'four', 5]
            cache.set('list_key', test_list)
            value = cache.get('list_key')
            
            assert value == test_list
            assert isinstance(value, list)
        else:
            pytest.skip("Redis not available")
    
    def test_cache_number(self):
        """Test caching numeric values"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            cache.set('int_key', 42)
            value = cache.get('int_key')
            
            assert value == 42
            
            cache.set('float_key', 3.14)
            value = cache.get('float_key')
            
            assert value == 3.14
        else:
            pytest.skip("Redis not available")


class TestCachePatterns:
    """Test pattern-based cache operations"""
    
    def test_delete_pattern(self):
        """Test deleting keys by pattern"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set multiple keys with same prefix
            cache.set('test:key1', 'value1')
            cache.set('test:key2', 'value2')
            cache.set('other:key', 'value3')
            
            # Delete by pattern
            deleted = cache.delete_pattern('test:*')
            
            assert deleted >= 2
            
            # Verify deletion
            assert cache.get('test:key1') is None
            assert cache.get('test:key2') is None
            # Other key should still exist
            assert cache.get('other:key') is not None
        else:
            pytest.skip("Redis not available")


class TestCacheHelpers:
    """Test cache helper methods"""
    
    def test_generate_key(self):
        """Test key generation from parts"""
        key = CacheService.generate_key('sentiment', 'deal', '123')
        
        assert key == 'sentiment:deal:123'
        assert isinstance(key, str)
    
    def test_generate_key_single_part(self):
        """Test key generation with single part"""
        key = CacheService.generate_key('simple')
        
        assert key == 'simple'
    
    def test_hash_text(self):
        """Test text hashing for cache keys"""
        text = "این یک متن تست است"
        hash1 = CacheService.hash_text(text)
        
        assert hash1 is not None
        assert len(hash1) == 32  # MD5 hash length
        
        # Same text should produce same hash
        hash2 = CacheService.hash_text(text)
        assert hash1 == hash2
        
        # Different text should produce different hash
        hash3 = CacheService.hash_text("متن متفاوت")
        assert hash1 != hash3
    
    def test_increment_counter(self):
        """Test incrementing a counter"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Increment counter
            value = cache.increment('test_counter', amount=1)
            assert value is not None
            
            # Increment again
            value2 = cache.increment('test_counter', amount=5)
            assert value2 == value + 5
        else:
            pytest.skip("Redis not available")
    
    def test_get_ttl(self):
        """Test getting TTL for a key"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Set key with TTL
            cache.set('test_ttl_check', 'value', ttl=300)
            
            ttl = cache.get_ttl('test_ttl_check')
            
            assert ttl is not None
            assert ttl > 0
            assert ttl <= 300
        else:
            pytest.skip("Redis not available")


class TestCacheStats:
    """Test cache statistics"""
    
    def test_get_stats(self):
        """Test getting cache statistics"""
        cache = CacheService(enabled=True)
        
        stats = cache.get_stats()
        
        assert isinstance(stats, dict)
        assert 'enabled' in stats
        assert 'available' in stats
        
        if cache.is_available():
            assert 'total_keys' in stats
            assert 'used_memory' in stats


class TestCacheGracefulDegradation:
    """Test cache graceful degradation when Redis unavailable"""
    
    def test_operations_with_redis_down(self):
        """Test that operations don't crash when Redis is down"""
        # Create cache with fake host
        cache = CacheService(host='invalid-host-xyz', enabled=True)
        
        # All operations should handle gracefully
        result = cache.set('key', 'value')
        assert result is False
        
        value = cache.get('key')
        assert value is None
        
        exists = cache.exists('key')
        assert exists is False
        
        deleted = cache.delete('key')
        assert deleted is False
    
    def test_disabled_cache_returns_safely(self):
        """Test disabled cache returns safe values"""
        cache = CacheService(enabled=False)
        
        # Set should return False
        assert cache.set('key', 'value') is False
        
        # Get should return None
        assert cache.get('key') is None
        
        # Exists should return False
        assert cache.exists('key') is False
        
        # Delete should return False
        assert cache.delete('key') is False


class TestCacheServiceSingleton:
    """Test global cache service singleton"""
    
    def test_get_cache_service_singleton(self):
        """Test getting global cache service instance"""
        cache1 = get_cache_service()
        cache2 = get_cache_service()
        
        # Should be same instance
        assert cache1 is cache2
    
    def test_cache_service_is_cache_service(self):
        """Test that singleton returns CacheService instance"""
        cache = get_cache_service()
        
        assert isinstance(cache, CacheService)
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'get')


class TestCacheRealWorldUsage:
    """Test real-world cache usage patterns"""
    
    def test_sentiment_caching_pattern(self):
        """Test typical sentiment result caching"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Simulate sentiment analysis result
            text = "این یک متن مثبت است"
            text_hash = cache.hash_text(text)
            cache_key = cache.generate_key('sentiment', text_hash)
            
            sentiment_result = {
                'sentiment': 'مثبت',
                'confidence': 0.95,
                'text_preview': text[:50]
            }
            
            # Cache result
            cache.set(cache_key, sentiment_result, ttl=3600)
            
            # Retrieve cached result
            cached = cache.get(cache_key)
            
            assert cached == sentiment_result
        else:
            pytest.skip("Redis not available")
    
    def test_analytics_caching_pattern(self):
        """Test typical analytics result caching"""
        cache = CacheService(enabled=True)
        
        if cache.is_available():
            # Simulate analytics result
            cache_key = cache.generate_key('deal_analysis', 'deal-123')
            
            analytics_result = {
                'health_score': 75,
                'risk_indicators': [],
                'insights': ['Good activity', 'Positive sentiment']
            }
            
            # Cache for 10 minutes
            cache.set(cache_key, analytics_result, ttl=600)
            
            # Retrieve
            cached = cache.get(cache_key)
            
            assert cached['health_score'] == 75
        else:
            pytest.skip("Redis not available")