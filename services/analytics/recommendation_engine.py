"""
services/analytics/recommendation_engine.py
-------------------------------------------
Single Responsibility: Generate actionable recommendations
"""

from typing import Dict, List, Any
from utils.logging_config import get_logger


class RecommendationEngine:
    """
    Generates actionable recommendations.
    
    Single Responsibility: Recommendations ONLY.
    """
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def generate(
        self, 
        deal: Dict[str, Any], 
        health_score: int,
        risk_indicators: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate recommendations based on deal state and risks.
        
        Args:
            deal: Deal data
            health_score: Health score
            risk_indicators: List of identified risks
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Priority recommendations from risks
        for risk in risk_indicators[:3]:
            rec = risk.get("recommendation", "")
            if rec and rec not in recommendations:
                recommendations.append(rec)
        
        # Health-based recommendations
        health_recs = self._get_health_recommendations(health_score)
        for rec in health_recs:
            if rec not in recommendations:
                recommendations.append(rec)
        
        # Ensure we have at least one recommendation
        if not recommendations:
            recommendations.append("ادامه پیگیری منظم معامله")
        
        return recommendations[:5]  # Max 5 recommendations
    
    def _get_health_recommendations(self, health_score: int) -> List[str]:
        """Get recommendations based on health score"""
        if health_score < 40:
            return [
                "بررسی دلایل ضعف معامله با مدیر",
                "ارزیابی احتمال موفقیت",
                "تصمیم‌گیری درباره ادامه یا توقف"
            ]
        elif health_score < 70:
            return [
                "افزایش تعامل با مشتری",
                "شناسایی موانع پیشرفت",
                "برنامه‌ریزی جلسه پیگیری"
            ]
        else:
            return [
                "حفظ momentum فعلی",
                "آماده‌سازی برای بستن معامله"
            ]