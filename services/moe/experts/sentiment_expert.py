"""
services/moe/experts/sentiment_expert.py
----------------------------------------
Expert for Persian text sentiment analysis.
REFACTORED: Uses centralized KeywordMatcher for can_handle().
"""

from typing import Any, Dict

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings
from utils.sentiment_utils import SentimentNormalizer


class SentimentExpert(BaseExpert):
    """Expert specializing in Persian text sentiment analysis"""

    @property
    def expert_type(self) -> str:
        return 'sentiment'

    @property
    def description(self) -> str:
        return "Analyzes sentiment and emotions in Persian and English text"

    @property
    def supported_query_types(self) -> list:
        return ['sentiment', 'emotion', 'feeling']

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this expert can handle the query.

        Uses centralized KeywordMatcher for consistent scoring.
        """
        matcher = self._get_keyword_matcher()
        return matcher.calculate_score(query, context)

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """Perform sentiment analysis"""
        context = context or {}

        # Get sentiment service
        sentiment_service = self.services.get('sentiment')
        if not sentiment_service:
            return ExpertResult.error_result(
                self.expert_type,
                "Sentiment service not available"
            )

        try:
            # Get text to analyze
            text_to_analyze = context.get('text', query)

            # Ensure model is loaded
            if not sentiment_service.model_loaded:
                self.logger.info("Loading sentiment model...")
                await sentiment_service.initialize()

            # Perform sentiment analysis
            result = sentiment_service.analyze_text(text_to_analyze)

            if not result or 'error' in result:
                return ExpertResult(
                    expert_type=self.expert_type,
                    success=False,
                    data=result or {'error': 'Analysis failed'},
                    confidence=0.0,
                    reasoning="Sentiment analysis failed"
                )

            confidence = self.calculate_confidence(query, result)

            # Normalize sentiment using centralized utility (DRY)
            sentiment = result.get('sentiment', 'neutral')
            normalized_sentiment = SentimentNormalizer.normalize(sentiment)

            return ExpertResult(
                expert_type=self.expert_type,
                success=True,
                data={
                    'text_analyzed': text_to_analyze[:200] + '...' if len(text_to_analyze) > 200 else text_to_analyze,
                    'sentiment': sentiment,
                    'normalized_sentiment': normalized_sentiment,
                    'confidence': result.get('confidence', 0.0),
                    'polarity': result.get('polarity', 0.0),
                    'subjectivity': result.get('subjectivity', 0.5)
                },
                confidence=confidence,
                reasoning=f"Text analyzed with sentiment: {sentiment}"
            )

        except Exception as e:
            self.logger.error(f"Sentiment analysis error: {e}")
            return ExpertResult.error_result(self.expert_type, str(e))

    