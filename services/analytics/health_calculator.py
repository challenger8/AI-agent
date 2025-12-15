"""
services/analytics/health_calculator.py
---------------------------------------
Single Responsibility: Calculate deal health scores
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.settings import AnalysisSettings
from config.constants import HealthCategory
from utils.logging_config import get_logger
from utils.deal_status_detector import DealStatusDetector
from utils.activity_utils import ActivityUtils
from utils.date_utils import DateUtils
from utils.sentiment_utils import SentimentNormalizer


class HealthCalculator:
    """
    Calculates health scores for deals.
    
    Single Responsibility: Health score calculation ONLY.
    Does NOT: Generate recommendations, identify risks, create insights.
    """
    
    def __init__(self, deal_service=None):
        self.logger = get_logger(self.__class__.__name__)
        self.deal_service = deal_service
    
    def calculate(
        self, 
        deal: Dict[str, Any], 
        activities: List[Any], 
        sentiment_summary: Dict[str, Any]
    ) -> int:
        """
        Calculate deal health score based on status.
        Routes to appropriate scoring method.
        
        Args:
            deal: Deal data
            activities: Deal activities
            sentiment_summary: Sentiment analysis summary
            
        Returns:
            Health score 0-100
        """
        status = self._detect_deal_status(deal)
        
        if status == 'won':
            return self._calculate_won(deal, activities)
        elif status == 'lost':
            return self._calculate_lost(deal, activities)
        elif status == 'open':
            return self._calculate_open(deal, activities, sentiment_summary)
        else:
            return 30  # Unknown status gets low score
    
    def get_category(self, score: int) -> str:
        """
        Get health category (English constant) from score.

        Returns English constant for use in code logic.
        Use get_category_persian() for UI display.

        Returns:
            One of: HealthCategory.HEALTHY, HealthCategory.MEDIUM, HealthCategory.AT_RISK
        """
        if score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return HealthCategory.HEALTHY
        elif score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return HealthCategory.MEDIUM
        else:
            return HealthCategory.AT_RISK

    def get_category_persian(self, score: int) -> str:
        """
        Get Persian health category label for UI display.

        Args:
            score: Health score (0-100)

        Returns:
            Persian category label: 'سالم', 'متوسط', or 'در خطر'
        """
        category = self.get_category(score)
        return HealthCategory.translate(category)
    
    def _detect_deal_status(self, deal: Dict[str, Any]) -> str:
        """
        Detect deal status from deal data.

        Delegates to centralized DealStatusDetector utility.
        """
        return DealStatusDetector.detect_string(deal)
    
    def _calculate_won(self, deal: Dict[str, Any], activities: List[Any]) -> int:
        """Calculate health score for WON deals (80-100)"""
        base_score = 85
        
        # Bonus for follow-up activities after close
        won_time = deal.get('change_to_won_time') or deal.get('ChangeToWonTime')
        if won_time and activities:
            post_close_activities = self._count_activities_after(activities, won_time)
            if post_close_activities > 0:
                base_score += min(post_close_activities * 3, 15)
        
        return min(base_score, 100)
    
    def _calculate_lost(self, deal: Dict[str, Any], activities: List[Any]) -> int:
        """Calculate health score for LOST deals (0-40)"""
        base_score = 20
        
        # Check if loss reason documented
        if deal.get('lost_reason_note') or deal.get('LostReasonNote'):
            base_score += 10
        
        # Check if learning activities happened
        if activities:
            base_score += min(len(activities), 10)
        
        return min(base_score, 40)
    
    def _calculate_open(
        self, 
        deal: Dict[str, Any], 
        activities: List[Any],
        sentiment_summary: Dict[str, Any]
    ) -> int:
        """Calculate health score for OPEN deals (0-100)"""
        score = 50  # Start at middle
        
        # Activity recency bonus/penalty
        if activities:
            days_since = self._days_since_last_activity(activities)
            if days_since <= 7:
                score += 20
            elif days_since <= 14:
                score += 10
            elif days_since > 30:
                score -= 20
            elif days_since > 60:
                score -= 35
        else:
            score -= 25  # No activities is bad
        
        # Activity volume bonus
        activity_count = len(activities) if activities else 0
        if activity_count >= 10:
            score += 15
        elif activity_count >= 5:
            score += 10
        elif activity_count < 2:
            score -= 10
        
        # Sentiment bonus/penalty using centralized normalizer (DRY)
        if sentiment_summary.get('sentiment_available'):
            dominant = sentiment_summary.get('dominant_sentiment', 'خنثی')
            score += SentimentNormalizer.get_score_modifier(
                dominant,
                positive_bonus=10,
                negative_penalty=15
            )
        
        return max(0, min(score, 100))
    
    def _count_activities_after(self, activities: List[Any], after_date) -> int:
        """
        Count activities after a given date.

        Delegates to centralized ActivityUtils utility.
        """
        cutoff = DateUtils.parse_iso_date(after_date)
        if not cutoff:
            return 0
        return ActivityUtils.count_activities_after(activities, cutoff)
    
    def _days_since_last_activity(self, activities: List[Any]) -> int:
        """
        Calculate days since last activity.

        Delegates to centralized ActivityUtils utility.
        """
        return ActivityUtils.days_since_last_activity(activities)