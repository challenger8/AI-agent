"""
services/analytics/health_calculator.py
---------------------------------------
Single Responsibility: Calculate deal health scores
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.settings import AnalysisSettings
from utils.logging_config import get_logger


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
        """Get health category label from score"""
        if score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return "سالم"
        elif score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return "متوسط"
        else:
            return "در خطر"
    
    def _detect_deal_status(self, deal: Dict[str, Any]) -> str:
        """Detect deal status from deal data"""
        # Check for won
        if deal.get('change_to_won_time') or deal.get('ChangeToWonTime'):
            return 'won'
        
        # Check for lost
        if deal.get('change_to_loss_time') or deal.get('ChangeToLossTime'):
            return 'lost'
        
        # Check status field
        status = deal.get('Status', deal.get('status', '')).lower()
        if status in ['بسته شده', 'won', 'closed_won']:
            return 'won'
        elif status in ['لغو شده', 'lost', 'closed_lost']:
            return 'lost'
        
        return 'open'
    
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
        
        # Sentiment bonus/penalty
        if sentiment_summary.get('sentiment_available'):
            dominant = sentiment_summary.get('dominant_sentiment', 'خنثی')
            if dominant in ['مثبت', 'positive']:
                score += 10
            elif dominant in ['منفی', 'negative']:
                score -= 15
        
        return max(0, min(score, 100))
    
    def _count_activities_after(self, activities: List[Any], after_date) -> int:
        """Count activities after a given date"""
        if isinstance(after_date, str):
            try:
                after_date = datetime.fromisoformat(after_date.replace('Z', '+00:00'))
            except:
                return 0
        
        count = 0
        for activity in activities:
            activity_date = getattr(activity, 'registerdate', None)
            if activity_date and activity_date > after_date:
                count += 1
        return count
    
    def _days_since_last_activity(self, activities: List[Any]) -> int:
        """Calculate days since last activity"""
        if not activities:
            return 999
        
        latest = None
        for activity in activities:
            activity_date = getattr(activity, 'registerdate', None)
            if activity_date:
                if latest is None or activity_date > latest:
                    latest = activity_date
        
        if latest:
            return (datetime.now() - latest).days
        return 999