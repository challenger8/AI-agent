"""
services/analytics/risk_analyzer.py
-----------------------------------
Single Responsibility: Identify and assess deal risks
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.settings import AnalysisSettings
from config.constants import RiskType, RiskSeverity, RecommendationType
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
            severity = RiskSeverity.HIGH if health_score < 25 else RiskSeverity.MEDIUM
            risks.append({
                "type": RiskType.LOW_HEALTH_SCORE,
                "severity": severity,
                "description": f"{RiskType.describe(RiskType.LOW_HEALTH_SCORE)}: {health_score}/100",
                "recommendation": RecommendationType.translate(RecommendationType.IMMEDIATE_REVIEW)
            })

        # Risk 2: Inactivity
        days_inactive = self._days_since_last_activity(activities)
        inactivity_risk = self._assess_inactivity_risk(days_inactive)
        if inactivity_risk:
            risks.append(inactivity_risk)

        # Risk 3: No activities at all
        if not activities:
            risks.append({
                "type": RiskType.NO_ACTIVITY,
                "severity": RiskSeverity.CRITICAL,
                "description": RiskType.describe(RiskType.NO_ACTIVITY),
                "recommendation": RecommendationType.translate(RecommendationType.START_ENGAGEMENT)
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
                "type": RiskType.CRITICAL_INACTIVITY,
                "severity": RiskSeverity.CRITICAL,
                "description": f"{RiskType.describe(RiskType.CRITICAL_INACTIVITY)}: {days} روز",
                "recommendation": RecommendationType.translate(RecommendationType.URGENT_FOLLOWUP)
            }
        elif days > AnalysisSettings.INACTIVITY_CONCERN_DAYS:  # > 30
            return {
                "type": RiskType.HIGH_INACTIVITY,
                "severity": RiskSeverity.HIGH,
                "description": f"{RiskType.describe(RiskType.HIGH_INACTIVITY)}: {days} روز",
                "recommendation": RecommendationType.translate(RecommendationType.URGENT_FOLLOWUP)
            }
        elif days > AnalysisSettings.INACTIVITY_WARNING_DAYS:  # > 14
            return {
                "type": RiskType.MODERATE_INACTIVITY,
                "severity": RiskSeverity.MEDIUM,
                "description": f"{RiskType.describe(RiskType.MODERATE_INACTIVITY)}: {days} روز",
                "recommendation": RecommendationType.translate(RecommendationType.SCHEDULE_ACTIVITY)
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
                "type": RiskType.DEAL_AGING,
                "severity": RiskSeverity.HIGH,
                "description": f"{RiskType.describe(RiskType.DEAL_AGING)}: {deal_age_days} روز",
                "recommendation": RecommendationType.translate(RecommendationType.REASSESS_SUCCESS)
            }
        elif deal_age_days > 90:  # 3 months
            return {
                "type": RiskType.DEAL_AGING,
                "severity": RiskSeverity.MEDIUM,
                "description": f"{RiskType.describe(RiskType.DEAL_AGING)}: {deal_age_days} روز",
                "recommendation": RecommendationType.translate(RecommendationType.REVIEW_OBSTACLES)
            }
        return None
    
    def _days_since_last_activity(self, activities: List[Any]) -> int:
        """
        Calculate days since last activity.

        Delegates to centralized ActivityUtils utility.
        """
        return ActivityUtils.days_since_last_activity(activities)