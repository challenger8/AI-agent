"""
services/analytics/insight_generator.py
---------------------------------------
Single Responsibility: Generate insights from analysis data
"""

from typing import Dict, List, Any
from config.settings import AnalysisSettings
from utils.logging_config import get_logger


class InsightGenerator:
    """
    Generates human-readable insights.
    
    Single Responsibility: Insight generation ONLY.
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def generate_deal_insights(
        self,
        deal: Dict[str, Any],
        activities: List[Any],
        sentiment_summary: Dict[str, Any],
        health_score: int,
        risk_indicators: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights for a single deal"""
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