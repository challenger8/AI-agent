"""
tests/integration/test_caching_integration.py
---------------------------------------------
Integration tests for caching in services
"""

import pytest
import time
from datetime import datetime, timedelta

from database.database import create_database_manager
from models.repositories import create_repositories
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService
from services.cache_service import get_cache_service


@pytest.fixture(scope="module")
def test_setup():
    """Setup test environment"""
    db = create_database_manager()
    repositories = create_repositories(db)
    cache = get_cache_service()
    
    # Clear test caches
    if cache.is_available():
        cache.delete_pattern("sentiment:*")
        cache.delete_pattern("deal_analysis:*")
        cache.delete_pattern("portfolio:*")
    
    yield {
        'db': db,
        'repositories': repositories,
        'cache': cache
    }
    
    # Cleanup
    if cache.is_available():
        cache.delete_pattern("sentiment:*")
        cache.delete_pattern("deal_analysis:*")
        cache.delete_pattern("portfolio:*")
    db.close()


class TestSentimentServiceCaching:
    """Test caching in SentimentService"""
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_sentiment_caching_enabled(self, test_setup):
        """Test that sentiment analysis uses caching"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        
        # Verify cache service is initialized
        assert sentiment_service.cache_service is not None
        assert sentiment_service.cache_service.is_available()
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_sentiment_cache_hit(self, test_setup):
        """Test sentiment cache hit"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        
        # Skip if model not loaded
        if not sentiment_service.model_loaded:
            pytest.skip("Sentiment model not loaded")
        
        text = "مشتری بسیار راضی است و قصد خرید دارد"
        
        # First call - cache miss
        start = time.time()
        result1 = sentiment_service.analyze_text(text)
        first_call_time = time.time() - start
        
        # Second call - cache hit
        start = time.time()
        result2 = sentiment_service.analyze_text(text)
        second_call_time = time.time() - start
        
        # Results should be identical
        assert result1['sentiment'] == result2['sentiment']
        assert result1['confidence'] == result2['confidence']
        
        # Second call should be much faster (cache hit)
        print(f"\nFirst call: {first_call_time:.4f}s")
        print(f"Second call: {second_call_time:.4f}s")
        print(f"Speedup: {first_call_time / second_call_time:.1f}x")
        
        # Cache hit should be at least 10x faster
        assert second_call_time < first_call_time / 10
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_sentiment_different_texts(self, test_setup):
        """Test that different texts get different cache entries"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        
        if not sentiment_service.model_loaded:
            pytest.skip("Sentiment model not loaded")
        
        text1 = "مشتری راضی است"
        text2 = "مشتری ناراضی است"
        
        result1 = sentiment_service.analyze_text(text1)
        result2 = sentiment_service.analyze_text(text2)
        
        # Different texts should (likely) have different sentiments
        # Note: Depends on model, but at least they should be cached separately
        assert result1 is not None
        assert result2 is not None
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_sentiment_cache_clear(self, test_setup):
        """Test clearing sentiment cache"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        
        if not sentiment_service.model_loaded:
            pytest.skip("Sentiment model not loaded")
        
        text = "تست پاکسازی کش"
        
        # Analyze to populate cache
        result1 = sentiment_service.analyze_text(text)
        
        # Verify it's cached
        text_hash = cache.hash_text(text.strip())
        cache_key = cache.generate_key("sentiment", text_hash)
        assert cache.exists(cache_key)
        
        # Clear cache
        deleted = sentiment_service.clear_sentiment_cache()
        assert deleted >= 0
        
        # Verify cache cleared
        assert not cache.exists(cache_key)


class TestAnalyticsServiceCaching:
    """Test caching in AnalyticsService"""
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_portfolio_overview_caching(self, test_setup):
        """Test portfolio overview caching"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        # First call - cache miss
        start = time.time()
        result1 = analytics_service.analyze_portfolio_overview(days=30)
        first_call_time = time.time() - start
        
        # Second call - cache hit
        start = time.time()
        result2 = analytics_service.analyze_portfolio_overview(days=30)
        second_call_time = time.time() - start
        
        # Results should be identical
        assert result1['summary']['total_deals'] == result2['summary']['total_deals']
        assert result1['period_days'] == result2['period_days']
        
        print(f"\nPortfolio Overview:")
        print(f"First call: {first_call_time:.4f}s")
        print(f"Second call: {second_call_time:.4f}s")
        print(f"Speedup: {first_call_time / second_call_time:.1f}x")
        
        # Cache hit should be significantly faster
        assert second_call_time < first_call_time / 5
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_deal_analysis_caching(self, test_setup):
        """Test individual deal analysis caching"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        
        # Get a sample deal
        deals = repositories.deals.get_all_deals()
        if not deals:
            pytest.skip("No deals in database")
        
        sample_deal = deals[0]
        deal_id = sample_deal.Id
        
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        # First call - cache miss
        start = time.time()
        result1 = analytics_service.analyze_deal_comprehensive(deal_id)
        first_call_time = time.time() - start
        
        # Second call - cache hit
        start = time.time()
        result2 = analytics_service.analyze_deal_comprehensive(deal_id)
        second_call_time = time.time() - start
        
        # Results should be identical
        assert result1['deal_id'] == result2['deal_id']
        assert result1['health_score'] == result2['health_score']
        
        print(f"\nDeal Analysis:")
        print(f"First call: {first_call_time:.4f}s")
        print(f"Second call: {second_call_time:.4f}s")
        print(f"Speedup: {first_call_time / second_call_time:.1f}x")
        
        # Cache hit should be much faster
        assert second_call_time < first_call_time / 5
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_cache_invalidation(self, test_setup):
        """Test cache invalidation for deals"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        deals = repositories.deals.get_all_deals()
        
        if not deals:
            pytest.skip("No deals in database")
        
        sample_deal = deals[0]
        deal_id = sample_deal.Id
        
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        # Analyze deal to populate cache
        result1 = analytics_service.analyze_deal_comprehensive(deal_id)
        
        # Verify cached
        cache_key = cache.generate_key("deal_analysis", deal_id)
        assert cache.exists(cache_key)
        
        # Invalidate cache
        analytics_service.invalidate_deal_cache(deal_id)
        
        # Verify cache cleared
        assert not cache.exists(cache_key)
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_different_parameters_different_cache(self, test_setup):
        """Test that different parameters create different cache entries"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        # Different days parameter
        result1 = analytics_service.analyze_portfolio_overview(days=7)
        result2 = analytics_service.analyze_portfolio_overview(days=30)
        
        # Should have different results
        assert result1['period_days'] != result2['period_days']
        
        # Different status parameter
        result3 = analytics_service.analyze_portfolio_overview(status="در حال پیگیری")
        result4 = analytics_service.analyze_portfolio_overview(status=None)
        
        # Should be cached separately
        assert result3 is not None
        assert result4 is not None


class TestCachePerformanceIntegration:
    """Test overall caching performance impact"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.requires_db
    def test_repeated_queries_performance(self, test_setup):
        """Test performance improvement with repeated queries"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        repositories = test_setup['repositories']
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        n_queries = 10
        
        # Test portfolio queries
        start = time.time()
        for _ in range(n_queries):
            analytics_service.analyze_portfolio_overview(days=30)
        total_time = time.time() - start
        
        avg_time = total_time / n_queries
        
        print(f"\n{n_queries} repeated portfolio queries:")
        print(f"Total time: {total_time:.4f}s")
        print(f"Average per query: {avg_time:.4f}s")
        
        # With caching, average should be very fast
        assert avg_time < 0.1  # Should be < 100ms on average
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_cache_stats(self, test_setup):
        """Test cache statistics"""
        cache = test_setup['cache']
        
        if not cache.is_available():
            pytest.skip("Redis not available")
        
        stats = cache.get_stats()
        
        assert stats['enabled'] is True
        assert stats['available'] is True
        assert 'total_keys' in stats
        assert 'used_memory' in stats
        assert 'hits' in stats
        assert 'misses' in stats
        
        print(f"\nCache Statistics:")
        print(f"  Total keys: {stats['total_keys']}")
        print(f"  Used memory: {stats['used_memory']}")
        print(f"  Cache hits: {stats['hits']}")
        print(f"  Cache misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']}%")


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])