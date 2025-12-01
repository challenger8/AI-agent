"""
tests/unit/test_cache_strategies.py
-----------------------------------
Tests for smart caching strategies
"""

import pytest
from services.cache_strategies import CacheTTLStrategy, get_smart_ttl


@pytest.mark.unit
class TestCacheTTLStrategy:
    """Test smart TTL calculations"""
    
    def test_open_deal_short_ttl(self):
        """Test that open deals get short TTL"""
        deal = {'Status': 'در حال پیگیری'}
        ttl = CacheTTLStrategy.get_deal_ttl(deal)
        
        assert ttl == 300  # 5 minutes
    
    def test_won_deal_long_ttl(self):
        """Test that won deals get long TTL"""
        deal = {'Status': 'بسته شده برنده'}
        ttl = CacheTTLStrategy.get_deal_ttl(deal)
        
        assert ttl == 3600  # 1 hour
    
    def test_lost_deal_long_ttl(self):
        """Test that lost deals get long TTL"""
        deal = {'Status': 'بسته شده بازنده'}
        ttl = CacheTTLStrategy.get_deal_ttl(deal)
        
        assert ttl == 3600  # 1 hour
    
    def test_deal_no_status_defaults_to_short(self):
        """Test that deals without status default to short TTL"""
        deal = {}
        ttl = CacheTTLStrategy.get_deal_ttl(deal)
        
        assert ttl == 300  # 5 minutes (safe default)
    
    def test_active_portfolio_short_ttl(self):
        """Test that active portfolio gets short TTL"""
        filters = {'status': 'active'}
        ttl = CacheTTLStrategy.get_portfolio_ttl(filters)
        
        assert ttl == 300  # 5 minutes
    
    def test_closed_portfolio_long_ttl(self):
        """Test that closed portfolio gets long TTL"""
        filters = {'status': 'won'}
        ttl = CacheTTLStrategy.get_portfolio_ttl(filters)
        
        assert ttl == 1800  # 30 minutes
    
    def test_sentiment_very_long_ttl(self):
        """Test that sentiment gets very long TTL (text doesn't change)"""
        ttl = CacheTTLStrategy.get_sentiment_ttl("test text")
        
        assert ttl == 86400  # 24 hours


@pytest.mark.unit
class TestSmartTTLHelper:
    """Test get_smart_ttl helper function"""
    
    def test_smart_ttl_deal(self):
        """Test smart TTL for deal"""
        deal = {'Status': 'Won'}
        ttl = get_smart_ttl('deal', deal)
        
        assert ttl == 3600
    
    def test_smart_ttl_portfolio(self):
        """Test smart TTL for portfolio"""
        ttl = get_smart_ttl('portfolio', {'status': 'active'})
        
        assert ttl == 300
    
    def test_smart_ttl_sentiment(self):
        """Test smart TTL for sentiment"""
        ttl = get_smart_ttl('sentiment')
        
        assert ttl == 86400
    
    def test_smart_ttl_unknown_defaults(self):
        """Test that unknown types get safe default"""
        ttl = get_smart_ttl('unknown_type')
        
        assert ttl == 300  # Safe default: 5 minutes