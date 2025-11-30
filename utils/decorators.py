# utils/decorators.py (CREATE or ADD to existing)
"""
Reusable decorators for common patterns
"""

from functools import wraps
from typing import Any, Dict, Callable
import logging

logger = logging.getLogger(__name__)


def requires_sentiment(error_response: Any = None):
    """
    Decorator that checks if sentiment service is available.
    
    Usage:
        @requires_sentiment({"error": "Sentiment not available"})
        def analyze_text(self, text):
            ...
    
    Args:
        error_response: What to return if sentiment unavailable
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check for sentiment service
            sentiment_svc = getattr(self, 'sentiment_service', None)
            
            if sentiment_svc is None:
                logger.warning(f"{func.__name__}: Sentiment service not available")
                return error_response or {"error": "Sentiment service not available"}
            
            if hasattr(sentiment_svc, 'model_loaded') and not sentiment_svc.model_loaded:
                logger.warning(f"{func.__name__}: Sentiment model not loaded")
                return error_response or {"error": "Sentiment model not loaded"}
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


def requires_service(service_name: str, error_response: Any = None):
    """
    Generic decorator for service availability check.
    
    Usage:
        @requires_service('analytics_service')
        def analyze_deal(self, deal_id):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            service = getattr(self, service_name, None)
            if service is None:
                logger.warning(f"{func.__name__}: {service_name} not available")
                return error_response or {"error": f"{service_name} not available"}
            return func(self, *args, **kwargs)
        return wrapper
    return decorator