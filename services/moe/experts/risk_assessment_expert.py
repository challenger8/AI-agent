"""
services/moe/experts/risk_assessment_expert.py
----------------------------------------------
Expert for risk evaluation and predictions.
REFACTORED: Uses centralized KeywordMatcher for can_handle().
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings
from config.settings import AnalysisSettings
from config.constants import RiskAnalysisConfig


class RiskAssessmentExpert(BaseExpert):
    """Expert specializing in risk evaluation and predictions"""

    @property
    def expert_type(self) -> str:
        return 'risk_assessment'

    @property
    def description(self) -> str:
        return "Evaluates risks, identifies threats, and predicts potential issues"

    @property
    def supported_query_types(self) -> list:
        return ['risk', 'warning', 'problem', 'threat']

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this expert can handle the query.

        Uses centralized KeywordMatcher for consistent scoring.
        """
        matcher = self._get_keyword_matcher()
        return matcher.calculate_score(query, context)

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """Perform risk assessment"""
        context = context or {}

        try:
            # Get deal ID if available
            deal_id = self._extract_deal_id(query, context)

            if deal_id:
                # Assess risks for specific deal
                result = await self._assess_deal_risks(deal_id)
            else:
                # Portfolio-wide risk assessment
                result = await self._assess_portfolio_risks()

            if 'error' in result:
                return ExpertResult(
                    expert_type=self.expert_type,
                    success=False,
                    data=result,
                    confidence=0.0,
                    reasoning=f"Risk assessment failed: {result['error']}"
                )

            confidence = self.calculate_confidence(query, result)

            return ExpertResult(
                expert_type=self.expert_type,
                success=True,
                data=result,
                confidence=confidence,
                reasoning=f"Identified {len(result.get('risk_indicators', []))} risk indicators"
            )

        except Exception as e:
            self.logger.error(f"Risk assessment error: {e}")
            return ExpertResult.error_result(self.expert_type, str(e))

    async def _assess_deal_risks(self, deal_id: str) -> Dict[str, Any]:
        """Assess risks for a specific deal"""
        # Get analytics service
        analytics_service = self.services.get('analytics')
        if not analytics_service:
            return {'error': 'Analytics service not available'}

        try:
            # Get deal analysis
            analysis = analytics_service.analyze_deal_comprehensive(deal_id)

            if 'error' in analysis:
                return analysis

            # Extract risk-related data
            risk_indicators = analysis.get('risk_indicators', [])
            health_score = analysis.get('health_score', 50)
            health_category = analysis.get('health_category', 'medium')

            # Calculate risk level
            risk_level = self._calculate_risk_level(health_score, risk_indicators)

            # Generate risk-specific recommendations
            recommendations = self._generate_risk_recommendations(
                risk_indicators, health_score, health_category
            )

            return {
                'deal_id': deal_id,
                'risk_level': risk_level,
                'risk_score': 100 - health_score,  # Inverse of health
                'risk_indicators': risk_indicators,
                'health_score': health_score,
                'health_category': health_category,
                'recommendations': recommendations,
                'mitigation_actions': self._suggest_mitigations(risk_indicators)
            }

        except Exception as e:
            return {'error': str(e)}

    async def _assess_portfolio_risks(self) -> Dict[str, Any]:
        """Assess risks across the entire portfolio"""
        # Get and validate services
        deal_service = self.services.get('deal')
        analytics_service = self.services.get('analytics')

        if not deal_service or not analytics_service:
            return {'error': 'Required services not available'}

        try:
            # Get all deals
            deals = deal_service.get_all_deals()

            if not deals:
                return {'total_deals': 0, 'message': 'No deals found'}

            # Categorize deals by risk level
            risk_categories = self._categorize_deals_by_risk(deals, analytics_service)

            # Build and return risk analysis
            return self._build_portfolio_risk_result(risk_categories)

        except Exception as e:
            return {'error': str(e)}

    def _categorize_deals_by_risk(
        self,
        deals: List[Dict[str, Any]],
        analytics_service: Any
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize deals into risk levels based on health scores.

        Args:
            deals: List of deals to analyze
            analytics_service: Analytics service for deal analysis

        Returns:
            Dictionary with 'high_risk', 'medium_risk', 'low_risk' lists
        """
        categories = {
            'high_risk': [],
            'medium_risk': [],
            'low_risk': []
        }

        # Analyze limited number of deals for performance
        for deal in deals[:RiskAnalysisConfig.MAX_DEALS_TO_ANALYZE]:
            deal_id = deal.get('id')
            if not deal_id:
                continue

            # Categorize deal by health score
            category_entry = self._analyze_and_categorize_deal(
                str(deal_id),
                analytics_service
            )

            if category_entry:
                risk_level = category_entry['risk_level']
                categories[f'{risk_level}_risk'].append(category_entry['data'])

        return categories

    def _analyze_and_categorize_deal(
        self,
        deal_id: str,
        analytics_service: Any
    ) -> Dict[str, Any] | None:
        """
        Analyze a single deal and determine its risk category.

        Args:
            deal_id: Deal identifier
            analytics_service: Analytics service

        Returns:
            Dictionary with risk_level and data, or None if analysis failed
        """
        try:
            analysis = analytics_service.analyze_deal_comprehensive(deal_id)
            health_score = analysis.get('health_score', 50)

            # Determine risk level
            if health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
                return {
                    'risk_level': 'high',
                    'data': {
                        'deal_id': deal_id,
                        'health_score': health_score,
                        'risks': analysis.get('risk_indicators', [])
                    }
                }
            elif health_score < AnalysisSettings.HEALTH_HIGH_THRESHOLD:
                return {
                    'risk_level': 'medium',
                    'data': {
                        'deal_id': deal_id,
                        'health_score': health_score
                    }
                }
            else:
                return {
                    'risk_level': 'low',
                    'data': {
                        'deal_id': deal_id,
                        'health_score': health_score
                    }
                }
        except Exception:
            return None

    def _build_portfolio_risk_result(
        self,
        risk_categories: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """
        Build final portfolio risk assessment result.

        Args:
            risk_categories: Categorized deals by risk level

        Returns:
            Portfolio risk analysis dictionary
        """
        high_risk = risk_categories['high_risk']
        medium_risk = risk_categories['medium_risk']
        low_risk = risk_categories['low_risk']

        total_analyzed = len(high_risk) + len(medium_risk) + len(low_risk)
        high_risk_percentage = (len(high_risk) / total_analyzed * 100) if total_analyzed > 0 else 0

        return {
            'total_deals_analyzed': total_analyzed,
            'high_risk_deals': high_risk,
            'high_risk_count': len(high_risk),
            'medium_risk_count': len(medium_risk),
            'low_risk_count': len(low_risk),
            'high_risk_percentage': round(high_risk_percentage, 1),
            'risk_summary': self._generate_portfolio_risk_summary(high_risk, total_analyzed),
            'priority_actions': self._generate_priority_actions(high_risk)
        }

    def _calculate_risk_level(self, health_score: int, risk_indicators: List[str]) -> str:
        """Calculate risk level based on health score and indicators"""
        risk_score = 100 - health_score
        indicator_penalty = len(risk_indicators) * 5

        total_risk = risk_score + indicator_penalty

        if total_risk >= 70:
            return 'high'
        elif total_risk >= 40:
            return 'medium'
        else:
            return 'low'

    def _generate_risk_recommendations(
        self,
        risk_indicators: List[str],
        health_score: int,
        health_category: str
    ) -> List[str]:
        """Generate risk-specific recommendations"""
        recommendations = []

        if health_score < 40:
            recommendations.append("Immediate attention required - deal health is critical")

        if any('inactivity' in r.lower() for r in risk_indicators):
            recommendations.append("Schedule follow-up activity within 24 hours")

        if any('sentiment' in r.lower() for r in risk_indicators):
            recommendations.append("Review recent communications for negative sentiment")

        if any('overdue' in r.lower() or 'delayed' in r.lower() for r in risk_indicators):
            recommendations.append("Review timeline and update stakeholders")

        if not recommendations:
            recommendations.append("Continue monitoring - no critical risks identified")

        return recommendations

    def _suggest_mitigations(self, risk_indicators: List[str]) -> List[Dict[str, str]]:
        """Suggest mitigation actions for each risk"""
        mitigations = []

        for indicator in risk_indicators:
            indicator_lower = indicator.lower()

            if 'inactivity' in indicator_lower:
                mitigations.append({
                    'risk': indicator,
                    'action': 'Schedule immediate follow-up call or meeting',
                    'priority': 'high'
                })
            elif 'sentiment' in indicator_lower:
                mitigations.append({
                    'risk': indicator,
                    'action': 'Review communications and address concerns',
                    'priority': 'high'
                })
            elif 'delayed' in indicator_lower or 'overdue' in indicator_lower:
                mitigations.append({
                    'risk': indicator,
                    'action': 'Update timeline and notify stakeholders',
                    'priority': 'medium'
                })
            else:
                mitigations.append({
                    'risk': indicator,
                    'action': 'Review and assess impact',
                    'priority': 'medium'
                })

        return mitigations

    def _generate_portfolio_risk_summary(
        self,
        high_risk_deals: List[Dict],
        total_analyzed: int
    ) -> str:
        """Generate summary of portfolio risks"""
        if not high_risk_deals:
            return "Portfolio health is good - no high-risk deals identified"

        percentage = len(high_risk_deals) / total_analyzed * 100 if total_analyzed > 0 else 0

        if percentage >= RiskAnalysisConfig.CRITICAL_RISK_PERCENTAGE:
            return f"Critical: {len(high_risk_deals)} deals ({percentage:.1f}%) are at high risk"
        elif percentage >= RiskAnalysisConfig.WARNING_RISK_PERCENTAGE:
            return f"Warning: {len(high_risk_deals)} deals ({percentage:.1f}%) need attention"
        else:
            return f"Moderate: {len(high_risk_deals)} deals require monitoring"

    def _generate_priority_actions(self, high_risk_deals: List[Dict]) -> List[str]:
        """Generate priority actions for high-risk deals"""
        if not high_risk_deals:
            return ["Continue regular monitoring"]

        actions = []
        sorted_deals = sorted(high_risk_deals, key=lambda x: x.get('health_score', 100))

        max_priority = RiskAnalysisConfig.MAX_HIGH_RISK_DEALS_TO_SHOW
        for deal in sorted_deals[:max_priority]:  # Top priority deals
            actions.append(f"Urgent: Review deal {deal['deal_id']} (health: {deal['health_score']})")

        if len(high_risk_deals) > max_priority:
            actions.append(f"Review remaining {len(high_risk_deals) - max_priority} high-risk deals")

        return actions

    @property
    def confidence_boost_keys(self) -> List[str]:
        return ['risk_indicators', 'recommendations', 'mitigation_actions']
    
