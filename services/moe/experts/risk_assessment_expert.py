"""
services/moe/experts/risk_assessment_expert.py
----------------------------------------------
Expert for risk evaluation and predictions
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings
from config.settings import AnalysisSettings


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
        """Determine if this expert can handle the query"""
        query_lower = query.lower()
        score = 0.0

        # Check for risk-related keywords
        risk_keywords = [
            'risk', 'ریسک', 'danger', 'خطر', 'warning', 'هشدار', 'problem', 'مشکل',
            'issue', 'concern', 'نگرانی', 'threat', 'تهدید', 'vulnerability', 'آسیب‌پذیری',
            'at risk', 'failing', 'delayed', 'تاخیر', 'lost', 'از دست رفته'
        ]

        for keyword in risk_keywords:
            if keyword in query_lower:
                score += 0.15

        # Check for risk-related patterns
        risk_patterns = [
            r'\bwhat.*risk\b',
            r'\bcheck.*risk\b',
            r'\brisk.*assessment\b',
            r'\bidentify.*problem\b'
        ]

        for pattern in risk_patterns:
            if re.search(pattern, query_lower):
                score += 0.2

        # Context boost
        if context and context.get('check_risks'):
            score += 0.3

        return min(score, 1.0)

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
        # Get deal service
        deal_service = self.services.get('deal')
        analytics_service = self.services.get('analytics')

        if not deal_service or not analytics_service:
            return {'error': 'Required services not available'}

        try:
            # Get all deals
            deals = deal_service.get_all_deals()

            if not deals:
                return {
                    'total_deals': 0,
                    'message': 'No deals found'
                }

            # Categorize by risk
            high_risk = []
            medium_risk = []
            low_risk = []

            for deal in deals[:50]:  # Limit for performance
                deal_id = deal.get('id')
                if not deal_id:
                    continue

                try:
                    analysis = analytics_service.analyze_deal_comprehensive(str(deal_id))
                    health_score = analysis.get('health_score', 50)

                    if health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
                        high_risk.append({
                            'deal_id': deal_id,
                            'health_score': health_score,
                            'risks': analysis.get('risk_indicators', [])
                        })
                    elif health_score < AnalysisSettings.HEALTH_HIGH_THRESHOLD:
                        medium_risk.append({
                            'deal_id': deal_id,
                            'health_score': health_score
                        })
                    else:
                        low_risk.append({
                            'deal_id': deal_id,
                            'health_score': health_score
                        })
                except Exception:
                    pass

            # Calculate overall risk metrics
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

        except Exception as e:
            return {'error': str(e)}

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

        if percentage >= 30:
            return f"Critical: {len(high_risk_deals)} deals ({percentage:.1f}%) are at high risk"
        elif percentage >= 15:
            return f"Warning: {len(high_risk_deals)} deals ({percentage:.1f}%) need attention"
        else:
            return f"Moderate: {len(high_risk_deals)} deals require monitoring"

    def _generate_priority_actions(self, high_risk_deals: List[Dict]) -> List[str]:
        """Generate priority actions for high-risk deals"""
        if not high_risk_deals:
            return ["Continue regular monitoring"]

        actions = []
        sorted_deals = sorted(high_risk_deals, key=lambda x: x.get('health_score', 100))

        for deal in sorted_deals[:3]:  # Top 3 priority
            actions.append(f"Urgent: Review deal {deal['deal_id']} (health: {deal['health_score']})")

        if len(high_risk_deals) > 3:
            actions.append(f"Review remaining {len(high_risk_deals) - 3} high-risk deals")

        return actions

    @property
    def confidence_boost_keys(self) -> List[str]:
        return ['risk_indicators', 'recommendations', 'mitigation_actions']
    
