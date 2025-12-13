"""
services/moe/experts/deal_analysis_expert.py
--------------------------------------------
Expert for deal health analysis and insights.
REFACTORED: Uses centralized KeywordMatcher for can_handle().
"""

from typing import Any, Dict, List

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
        """
        Determine if this expert can handle the query.

        Uses centralized KeywordMatcher for consistent scoring.
        """
        matcher = self._get_keyword_matcher()
        return matcher.calculate_score(query, context)

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

    @property
    def confidence_boost_keys(self) -> List[str]:
        return ['health_score', 'recommendations', 'insights', 'risk_indicators']
    
