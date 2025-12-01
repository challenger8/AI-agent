"""
services/cache_strategies.py
---------------------------
Smart caching strategies for different data types
"""

from typing import Dict, Any


class CacheTTLStrategy:
    """Determine appropriate TTL based on data characteristics"""
    
    # Base TTLs (in seconds)
    DEAL_OPEN_TTL = 300         # 5 minutes (changes frequently)
    DEAL_WON_TTL = 3600         # 1 hour (rarely changes)
    DEAL_LOST_TTL = 3600        # 1 hour (rarely changes)
    PORTFOLIO_ACTIVE_TTL = 300  # 5 minutes (active portfolio changes)
    PORTFOLIO_CLOSED_TTL = 1800 # 30 minutes (historical data)
    SENTIMENT_TTL = 86400       # 24 hours (text doesn't change)
    ACTIVITY_LIST_TTL = 300     # 5 minutes (grows over time)
    AGENT_TTL = 1800            # 30 minutes (rarely changes)
    
    @staticmethod
    def get_deal_ttl(deal: Dict[str, Any]) -> int:
        """
        Calculate appropriate TTL for deal cache based on status
        
        Args:
            deal: Deal dictionary
            
        Returns:
            TTL in seconds
            
        Logic:
            - Closed deals (Won/Lost) rarely change → cache longer (1 hour)
            - Open deals change frequently → cache shorter (5 minutes)
        """
        status = deal.get('Status', '').lower()
        
        # Check for closed status (Won)
        if any(word in status for word in ['won', 'برنده', 'بسته شده برنده']):
            return CacheTTLStrategy.DEAL_WON_TTL
        
        # Check for closed status (Lost)
        if any(word in status for word in ['lost', 'بازنده', 'بسته شده بازنده']):
            return CacheTTLStrategy.DEAL_LOST_TTL
        
        # Open/Active deals (default)
        return CacheTTLStrategy.DEAL_OPEN_TTL
    
    @staticmethod
    def get_portfolio_ttl(filters: Dict[str, Any] = None) -> int:
        """
        Calculate TTL for portfolio cache based on filters
        
        Args:
            filters: Portfolio filter parameters (status, days, etc.)
            
        Returns:
            TTL in seconds
            
        Logic:
            - Historical/closed portfolios change less → cache longer
            - Active portfolios change more → cache shorter
        """
        if not filters:
            return CacheTTLStrategy.PORTFOLIO_ACTIVE_TTL
        
        status = filters.get('status', '').lower()
        
        # Historical data (won/lost deals)
        if status in ['won', 'lost', 'closed']:
            return CacheTTLStrategy.PORTFOLIO_CLOSED_TTL
        
        # Active portfolio
        return CacheTTLStrategy.PORTFOLIO_ACTIVE_TTL
    
    @staticmethod
    def get_sentiment_ttl(text: str = None) -> int:
        """
        Sentiment for same text never changes
        
        Args:
            text: Text being analyzed (not used, but kept for API consistency)
            
        Returns:
            TTL in seconds (24 hours)
        """
        return CacheTTLStrategy.SENTIMENT_TTL
    
    @staticmethod
    def get_activity_list_ttl() -> int:
        """
        Activity lists change as new activities are added
        
        Returns:
            TTL in seconds (5 minutes)
        """
        return CacheTTLStrategy.ACTIVITY_LIST_TTL


# Convenience function
def get_smart_ttl(data_type: str, data: Dict[str, Any] = None) -> int:
    """
    Get smart TTL for any data type
    
    Args:
        data_type: Type of data ('deal', 'portfolio', 'sentiment', 'activity')
        data: Data object (optional, used for context)
        
    Returns:
        TTL in seconds
        
    Example:
        ttl = get_smart_ttl('deal', deal_dict)
        ttl = get_smart_ttl('portfolio', {'status': 'Won'})
    """
    if data_type == 'deal' and data:
        return CacheTTLStrategy.get_deal_ttl(data)
    elif data_type == 'portfolio':
        return CacheTTLStrategy.get_portfolio_ttl(data or {})
    elif data_type == 'sentiment':
        return CacheTTLStrategy.get_sentiment_ttl()
    elif data_type == 'activity':
        return CacheTTLStrategy.get_activity_list_ttl()
    else:
        # Default: 5 minutes
        return 300