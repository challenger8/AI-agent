"""
services/analytics/risk_analyzer.py
-----------------------------------
Single Responsibility: Identify and assess deal risks
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.settings import AnalysisSettings
from utils.logging_config import get_logger
from utils.activity_utils import ActivityUtils
from utils.date_utils import DateUtils


class RiskAnalyzer:
    """
    Identifies and assesses deal risks.
    
    Single Responsibility: Risk detection ONLY.
    Does NOT: Calculate health scores, generate recommendations.
    """
    
    def __init__(self, deal_service=None):
        self.logger = get_logger(self.__class__.__name__)
        self.deal_service = deal_service
    
    def identify_risks(
        self, 
        deal: Dict[str, Any], 
        activities: List[Any], 
        health_score: int
    ) -> List[Dict[str, Any]]:
        """
        Identify risk indicators for a deal.
        
        Args:
            deal: Deal data
            activities: Deal activities  
            health_score: Pre-calculated health score
            
        Returns:
            List of risk dictionaries
        """
        risks = []
        
        # Risk 1: Low health score
        if health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            risks.append({
                "type": "low_health_score",
                "severity": "high" if health_score < 25 else "medium",
                "description": f"امتیاز سلامت پایین: {health_score}/100",
                "recommendation": "بازبینی فوری استراتژی معامله"
            })
        
        # Risk 2: Inactivity
        days_inactive = self._days_since_last_activity(activities)
        inactivity_risk = self._assess_inactivity_risk(days_inactive)
        if inactivity_risk:
            risks.append(inactivity_risk)
        
        # Risk 3: No activities at all
        if not activities:
            risks.append({
                "type": "no_activity",
                "severity": "critical",
                "description": "هیچ فعالیتی ثبت نشده",
                "recommendation": "شروع فوری تعامل با مشتری"
            })
        
        # Risk 4: Deal aging (for open deals)
        aging_risk = self._assess_aging_risk(deal)
        if aging_risk:
            risks.append(aging_risk)
        
        return risks
    
    def _assess_inactivity_risk(self, days: int) -> Dict[str, Any] | None:
        """Assess risk based on days of inactivity"""
        if days > AnalysisSettings.INACTIVITY_CRITICAL_DAYS:  # > 60
            return {
                "type": "critical_inactivity",
                "severity": "critical",
                "description": f"عدم فعالیت: {days} روز",
                "recommendation": "پیگیری اضطراری"
            }
        elif days > AnalysisSettings.INACTIVITY_CONCERN_DAYS:  # > 30
            return {
                "type": "high_inactivity",
                "severity": "high",
                "description": f"عدم فعالیت: {days} روز",
                "recommendation": "پیگیری فوری"
            }
        elif days > AnalysisSettings.INACTIVITY_WARNING_DAYS:  # > 14
            return {
                "type": "moderate_inactivity",
                "severity": "medium",
                "description": f"عدم فعالیت: {days} روز",
                "recommendation": "برنامه‌ریزی جلسه"
            }
        return None
    
    def _assess_aging_risk(self, deal: Dict[str, Any]) -> Dict[str, Any] | None:
        """
        Assess risk based on deal age.

        Uses centralized DateUtils for date parsing.
        """
        register_time = deal.get('register_time') or deal.get('RegisterTime')
        if not register_time:
            return None

        parsed_time = DateUtils.parse_iso_date(register_time)
        if not parsed_time:
            return None

        deal_age_days = DateUtils.days_since(parsed_time)

        if deal_age_days > 180:  # 6 months
            return {
                "type": "deal_aging",
                "severity": "high",
                "description": f"معامله قدیمی: {deal_age_days} روز",
                "recommendation": "ارزیابی مجدد احتمال موفقیت"
            }
        elif deal_age_days > 90:  # 3 months
            return {
                "type": "deal_aging",
                "severity": "medium",
                "description": f"معامله طولانی: {deal_age_days} روز",
                "recommendation": "بررسی موانع پیشرفت"
            }
        return None
    
    def _days_since_last_activity(self, activities: List[Any]) -> int:
        """
        Calculate days since last activity.

        Delegates to centralized ActivityUtils utility.
        """
        return ActivityUtils.days_since_last_activity(activities)