"""
services/moe/experts/sentiment_expert.py
----------------------------------------
Expert for Persian text sentiment analysis
"""

from typing import Any, Dict

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings


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
        """Determine if this expert can handle the query"""
        query_lower = query.lower()
        score = 0.0

        # Check for sentiment-related keywords
        sentiment_keywords = [
            'sentiment', 'احساس', 'feeling', 'emotion', 'حس', 'mood', 'خلق',
            'positive', 'مثبت', 'negative', 'منفی', 'neutral', 'خنثی',
            'opinion', 'نظر', 'tone', 'لحن'
        ]

        for keyword in sentiment_keywords:
            if keyword in query_lower:
                score += 0.15

        # Check if query is in Persian (likely wants sentiment analysis)
        persian_chars = len([c for c in query if '\u0600' <= c <= '\u06FF'])
        if persian_chars > len(query) * 0.3:
            score += 0.2

        # Context boost
        if context and context.get('analyze_sentiment'):
            score += 0.3

        return min(score, 1.0)

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

            # Map sentiment to emoji for display
            sentiment = result.get('sentiment', 'neutral')
            emoji_map = {
                'positive': 'positive',
                'مثبت': 'positive',
                'negative': 'negative',
                'منفی': 'negative',
                'neutral': 'neutral',
                'خنثی': 'neutral'
            }

            normalized_sentiment = emoji_map.get(sentiment, 'neutral')

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

    def calculate_confidence(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the result"""
        base_confidence = 0.6

        # Use model's confidence if available
        model_confidence = result.get('confidence', 0.5)
        base_confidence = max(base_confidence, model_confidence)

        # Boost for clear sentiment (not neutral)
        sentiment = result.get('sentiment', 'neutral')
        if sentiment in ['positive', 'negative', 'مثبت', 'منفی']:
            base_confidence += 0.1

        # Boost for high model confidence
        if model_confidence > 0.8:
            base_confidence += 0.1

        return min(base_confidence, 1.0)
