"""
utils/health_categorizer.py
---------------------------
Unified health score categorization utilities.

DRY: Consolidates 30+ lines of duplicate health score → risk level
categorization found across 3 service files:
- services/analytics/risk_analyzer.py
- services/moe/experts/risk_assessment_expert.py
- services/analytics/insight_generator.py
"""

from typing import Dict, Any, Optional, List
from config.settings import AnalysisSettings


class HealthCategorizer:
    """
    Centralized health score categorization and risk level mapping.

    Provides consistent mapping between health scores and risk levels
    across all analytics and expert systems.

    DRY: Eliminates duplicate threshold checking scattered across
    multiple analytics and expert files.
    """

    @staticmethod
    def get_risk_level(health_score: int) -> str:
        """
        Get risk level from health score.

        DRY: Replaces duplicate threshold checks in:
        - services/analytics/risk_analyzer.py:49
        - services/moe/experts/risk_assessment_expert.py:204-228
        - services/analytics/insight_generator.py:119-133

        Args:
            health_score: Health score (0-100)

        Returns:
            Risk level: 'high', 'medium', or 'low'

        Examples:
            >>> HealthCategorizer.get_risk_level(30)
            'high'
            >>> HealthCategorizer.get_risk_level(75)
            'medium'
            >>> HealthCategorizer.get_risk_level(85)
            'low'
        """
        if health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return 'high'
        elif health_score < AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return 'medium'
        return 'low'

    @staticmethod
    def get_category(health_score: int) -> str:
        """
        Get health category from score.

        Args:
            health_score: Health score (0-100)

        Returns:
            Category: 'critical', 'low', 'medium', or 'high'

        Examples:
            >>> HealthCategorizer.get_category(20)
            'critical'
            >>> HealthCategorizer.get_category(50)
            'low'
            >>> HealthCategorizer.get_category(75)
            'medium'
            >>> HealthCategorizer.get_category(90)
            'high'
        """
        if health_score < 40:
            return 'critical'
        elif health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return 'low'
        elif health_score < AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return 'medium'
        return 'high'

    @staticmethod
    def is_critical(health_score: int) -> bool:
        """Check if health score is critical (<40)"""
        return health_score < 40

    @staticmethod
    def is_low(health_score: int) -> bool:
        """Check if health score is low (40-69)"""
        return 40 <= health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD

    @staticmethod
    def is_medium(health_score: int) -> bool:
        """Check if health score is medium (70-79)"""
        return (AnalysisSettings.HEALTH_MEDIUM_THRESHOLD <= health_score <
                AnalysisSettings.HEALTH_HIGH_THRESHOLD)

    @staticmethod
    def is_high(health_score: int) -> bool:
        """Check if health score is high (80+)"""
        return health_score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD

    @staticmethod
    def get_risk_data(
        health_score: int,
        deal_id: Optional[str] = None,
        risk_indicators: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Get categorization with additional risk data.

        DRY: Consolidates the risk data structure pattern from:
        - services/moe/experts/risk_assessment_expert.py:204-228

        Args:
            health_score: Health score (0-100)
            deal_id: Optional deal ID
            risk_indicators: Optional list of risk indicators

        Returns:
            Dictionary with risk level and data:
                {
                    'risk_level': str,
                    'data': {
                        'deal_id': str (if provided),
                        'health_score': int,
                        'risks': list (if provided)
                    }
                }

        Examples:
            >>> HealthCategorizer.get_risk_data(30, 'deal-123')
            {'risk_level': 'high', 'data': {'deal_id': 'deal-123', 'health_score': 30}}
        """
        data = {'health_score': health_score}

        if deal_id:
            data['deal_id'] = deal_id

        if risk_indicators:
            data['risks'] = risk_indicators

        return {
            'risk_level': HealthCategorizer.get_risk_level(health_score),
            'data': data
        }

    @staticmethod
    def get_severity(health_score: int) -> str:
        """
        Get severity level for risk indicators.

        Used by risk_analyzer.py to determine severity.

        Args:
            health_score: Health score (0-100)

        Returns:
            Severity: 'HIGH', 'MEDIUM', or 'LOW'

        Examples:
            >>> HealthCategorizer.get_severity(20)
            'HIGH'
            >>> HealthCategorizer.get_severity(40)
            'MEDIUM'
        """
        if health_score < 25:
            return 'HIGH'
        elif health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return 'MEDIUM'
        return 'LOW'

    @staticmethod
    def get_persian_status_message(health_score: int) -> str:
        """
        Get Persian status message for health score.

        DRY: Consolidates Persian message generation from:
        - services/analytics/insight_generator.py:119-133

        Args:
            health_score: Health score (0-100)

        Returns:
            Persian status message

        Examples:
            >>> HealthCategorizer.get_persian_status_message(90)
            '✅ معامله سالم: 90/100'
        """
        if health_score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return f"✅ معامله سالم: {health_score}/100"
        elif health_score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return f"⚠️ وضعیت متوسط: {health_score}/100"
        else:
            return f"🔴 معامله در خطر: {health_score}/100"
