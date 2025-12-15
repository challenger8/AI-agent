"""
services/analytics/insight_generator.py
---------------------------------------
Single Responsibility: Generate insights from analysis data

KISS REFACTOR: Uses context dataclasses to reduce parameter coupling
"""

from typing import Dict, List, Any, Union
from config.settings import AnalysisSettings
from utils.logging_config import get_logger
from services.analytics.context import DealAnalysisContext


class InsightGenerator:
    """
    Generates human-readable insights.

    Single Responsibility: Insight generation ONLY.
    KISS: Uses context objects for cleaner signatures.
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def generate_deal_insights(
        self,
        context: Union[DealAnalysisContext, Dict[str, Any]] = None,
        # Legacy parameters for backward compatibility
        deal: Dict[str, Any] = None,
        activities: List[Any] = None,
        sentiment_summary: Dict[str, Any] = None,
        health_score: int = None,
        risk_indicators: List[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Generate insights for a single deal.

        REFACTORED: Supports both context object and individual parameters.

        Args:
            context: DealAnalysisContext object (preferred)
            deal: Deal dict (legacy, use context instead)
            activities: Activities list (legacy, use context instead)
            sentiment_summary: Sentiment summary (legacy, use context instead)
            health_score: Health score (legacy, use context instead)
            risk_indicators: Risk indicators (legacy, use context instead)

        Returns:
            List of insight strings
        """
        # Support both new (context) and old (individual params) APIs
        if isinstance(context, DealAnalysisContext):
            deal = context.deal
            activities = context.activities
            sentiment_summary = context.sentiment_summary
            health_score = context.health_score
            risk_indicators = context.risk_indicators
        elif context is not None and isinstance(context, dict):
            # If first param is a dict, assume it's legacy 'deal' parameter
            # Shift all parameters
            risk_indicators = health_score
            health_score = sentiment_summary
            sentiment_summary = activities
            activities = deal
            deal = context
        insights = []
        
        # Health insight
        insights.extend(self._health_insights(health_score))
        
        # Activity insights
        insights.extend(self._activity_insights(activities))
        
        # Sentiment insights
        insights.extend(self._sentiment_insights(sentiment_summary))
        
        # Risk insights
        if risk_indicators:
            high_risks = [r for r in risk_indicators if r.get("severity") == "high"]
            if high_risks:
                insights.append(f"⚠️ {len(high_risks)} خطر با اولویت بالا شناسایی شد")
        
        return insights
    
    def generate_portfolio_insights(
        self,
        summary: Dict,
        activity_breakdown: Dict,
        sentiment_overview: Dict,
        health_overview: Dict
    ) -> List[str]:
        """Generate portfolio-level insights"""
        insights = []
        
        # Activity rate insight
        activity_rate = summary.get("activity_rate", 0)
        if activity_rate >= 70:
            insights.append(f"✅ نرخ فعالیت بالا: {activity_rate}%")
        elif activity_rate < 40:
            insights.append(f"⚠️ نرخ فعالیت پایین: {activity_rate}%")
        
        # Health insights
        avg_health = health_overview.get("average_health_score", 0)
        at_risk = health_overview.get("at_risk_count", 0)
        
        if avg_health >= 70:
            insights.append(f"💪 سلامت پورتفولیو خوب: {avg_health}/100")
        elif avg_health < 50:
            insights.append(f"⚠️ سلامت پورتفولیو نیاز به توجه: {avg_health}/100")
        
        if at_risk > 0:
            insights.append(f"🔴 {at_risk} معامله در خطر")
        
        return insights
    
    def _health_insights(self, health_score: int) -> List[str]:
        """Generate health-related insights"""
        if health_score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return [
                f"✅ معامله سالم: {health_score}/100",
                "💡 فرصت مناسب برای بستن معامله"
            ]
        elif health_score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return [
                f"⚠️ وضعیت متوسط: {health_score}/100",
                "💡 نیاز به افزایش تعامل"
            ]
        else:
            return [
                f"🔴 معامله در خطر: {health_score}/100",
                "💡 بازبینی فوری استراتژی لازم است"
            ]
    
    def _activity_insights(self, activities: List[Any]) -> List[str]:
        """Generate activity-related insights"""
        if not activities:
            return ["⚠️ هیچ فعالیتی ثبت نشده"]
        
        count = len(activities)
        if count >= 10:
            return [f"📈 تعامل خوب: {count} فعالیت"]
        elif count < 3:
            return [f"⚠️ تعامل کم: {count} فعالیت"]
        return []
    
    def _sentiment_insights(self, sentiment_summary: Dict) -> List[str]:
        """Generate sentiment-related insights"""
        if not sentiment_summary.get("sentiment_available"):
            return []
        
        dominant = sentiment_summary.get("dominant_sentiment", "خنثی")
        
        if dominant in ["مثبت", "positive"]:
            return ["😊 احساسات مثبت در تعاملات"]
        elif dominant in ["منفی", "negative"]:
            return ["😟 احساسات منفی - رفع نگرانی‌ها"]
        return []