"""
services/moe/experts/deal_analysis_expert.py
--------------------------------------------
Expert for deal health analysis and insights
"""

import re
from typing import Any, Dict

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings


class DealAnalysisExpert(BaseExpert):
    """Expert specializing in deal health analysis and insights"""

    @property
    def expert_type(self) -> str:
        return 'deal_analysis'

    @property
    def description(self) -> str:
        return "Analyzes deal health, performance metrics, and provides strategic insights"

    @property
    def supported_query_types(self) -> list:
        return ['deal_analysis', 'performance', 'health']

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """Determine if this expert can handle the query"""
        query_lower = query.lower()
        score = 0.0

        # Check for deal-related keywords
        deal_keywords = [
            'deal', 'معامله', 'قرارداد', 'health', 'سلامت', 'score', 'امتیاز',
            'analyze', 'تحلیل', 'performance', 'عملکرد', 'status', 'وضعیت'
        ]

        for keyword in deal_keywords:
            if keyword in query_lower:
                score += 0.15

        # Check for deal ID pattern
        if re.search(r'\bdeal[\s_-]?\d+\b|\bدیل[\s_-]?\d+\b', query_lower):
            score += 0.3

        # Context boost
        if context and context.get('entity_type') == 'deal':
            score += 0.2

        return min(score, 1.0)

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """Perform deal analysis"""
        context = context or {}

        # Get analytics service
        analytics_service = self.services.get('analytics')
        if not analytics_service:
            return ExpertResult.error_result(
                self.expert_type,
                "Analytics service not available"
            )

        try:
            # Extract deal ID from query or context
            deal_id = self._extract_deal_id(query, context)

            if deal_id:
                # Analyze specific deal
                result = analytics_service.analyze_deal_comprehensive(deal_id)

                if 'error' in result:
                    return ExpertResult(
                        expert_type=self.expert_type,
                        success=False,
                        data=result,
                        confidence=0.0,
                        reasoning=f"Deal analysis failed: {result['error']}"
                    )

                confidence = self.calculate_confidence(query, result)

                return ExpertResult(
                    expert_type=self.expert_type,
                    success=True,
                    data={
                        'deal_id': deal_id,
                        'health_score': result.get('health_score', 0),
                        'health_category': result.get('health_category', 'unknown'),
                        'risk_indicators': result.get('risk_indicators', []),
                        'recommendations': result.get('recommendations', []),
                        'insights': result.get('insights', {}),
                        'activities_count': result.get('activities', {}).get('total_count', 0),
                        'sentiment_summary': result.get('sentiment_analysis', {})
                    },
                    confidence=confidence,
                    reasoning=f"Analyzed deal {deal_id} with health score {result.get('health_score', 0)}"
                )
            else:
                # Portfolio analysis
                result = analytics_service.analyze_portfolio_overview()

                if 'error' in result:
                    return ExpertResult(
                        expert_type=self.expert_type,
                        success=False,
                        data=result,
                        confidence=0.0,
                        reasoning=f"Portfolio analysis failed: {result['error']}"
                    )

                confidence = self.calculate_confidence(query, result)

                return ExpertResult(
                    expert_type=self.expert_type,
                    success=True,
                    data={
                        'type': 'portfolio_overview',
                        'summary': result.get('summary', {}),
                        'status_distribution': result.get('status_distribution', {}),
                        'health_metrics': result.get('health_metrics', {}),
                        'insights': result.get('insights', [])
                    },
                    confidence=confidence,
                    reasoning="Portfolio overview analysis completed"
                )

        except Exception as e:
            self.logger.error(f"Deal analysis error: {e}")
            return ExpertResult.error_result(self.expert_type, str(e))

    def calculate_confidence(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the result"""
        base_confidence = 0.7

        # Boost for successful result with data
        if result and 'error' not in result:
            base_confidence += 0.1

        # Boost for health score present
        if 'health_score' in result:
            base_confidence += 0.1

        # Boost for recommendations
        if result.get('recommendations'):
            base_confidence += 0.05

        # Boost for insights
        if result.get('insights'):
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _extract_deal_id(self, query: str, context: Dict[str, Any]) -> str:
        """Extract deal ID from query or context"""
        # Check context first
        if context.get('deal_id'):
            return str(context['deal_id'])

        # Try to extract from query
        patterns = [
            r'\bdeal[\s_-]?(\d+)\b',
            r'\bدیل[\s_-]?(\d+)\b',
            r'\b(\d+)\b'  # Fallback to any number
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
