"""
services/analytics_service.py
-----------------------------
Advanced analytics and health metrics service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from services.base_service import BaseService
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from config.settings import AnalysisSettings
from utils.exceptions import ServiceError

class AnalyticsService(BaseService):
    """Advanced analytics combining deals, activities, and sentiment"""
    
    def __init__(self, repositories=None, sentiment_service: Optional[SentimentService] = None):
        super().__init__(repositories)
        self.deal_service = DealService(repositories)
        self.sentiment_service = sentiment_service
    
    def analyze_deal_comprehensive(self, deal_id: int) -> Dict[str, Any]:
        """
        Comprehensive
        """